#!/usr/bin/env python3
"""
Process ERA5-Land GeoTIFF data and integrate with IndiaWeatherBench HDF5 files.

This script handles all format conversions:
1. Reads GeoTIFF files (monthly means, 6 bands per file)
2. Converts heat fluxes from accumulated J/m² to average W/m²
3. Regrids from 322×321 @ 0.1° to 256×256 @ 0.12° using bilinear interpolation
4. Crops to exact IndiaWeatherBench domain
5. Replicates monthly means to all 6-hourly timesteps in that month
6. Integrates into existing HDF5 files (adds new variables)

Input: GeoTIFF files (era5_land_YYYY_MM.tif)
Output: Updated HDF5 files with 6 new variables
"""

import os
import argparse
import numpy as np
import rasterio
import h5py
from scipy import interpolate
from datetime import datetime, timedelta
from tqdm import tqdm
import calendar
import warnings

warnings.filterwarnings('ignore')


# IndiaWeatherBench domain specifications
IWB_LAT_START = 6.0
IWB_LAT_END = 36.72
IWB_LON_START = 66.6
IWB_LON_END = 97.25
IWB_GRID_SIZE = 256


# Band mapping (verified from GEE)
BAND_MAPPING = {
    1: 'swvl1',      # Soil moisture layer 1
    2: 'swvl2',      # Soil moisture layer 2
    3: 'slhf',       # Surface latent heat flux (accumulated)
    4: 'sshf',       # Surface sensible heat flux (accumulated)
    5: 'lai_hv',     # LAI high vegetation
    6: 'lai_lv'      # LAI low vegetation
}

# Variables that need conversion from accumulated J/m² to average W/m²
FLUX_VARIABLES = ['slhf', 'sshf']


def create_iwb_grid():
    """Create the target IndiaWeatherBench grid (256×256 @ 0.12°)."""
    lats = np.linspace(IWB_LAT_START, IWB_LAT_END, IWB_GRID_SIZE)
    lons = np.linspace(IWB_LON_START, IWB_LON_END, IWB_GRID_SIZE)
    return lats, lons


def extract_coordinates_from_geotiff(src):
    """Extract latitude and longitude arrays from GeoTIFF."""
    # Get coordinates for each pixel center
    lons = np.array([src.xy(0, j)[0] for j in range(src.width)])
    lats = np.array([src.xy(i, 0)[1] for i in range(src.height)])
    return lats, lons


def regrid_bilinear(data_2d, source_lats, source_lons, target_lats, target_lons):
    """
    Regrid data using bilinear interpolation.
    
    Args:
        data_2d: 2D array (source_height, source_width)
        source_lats: Source latitudes (1D array)
        source_lons: Source longitudes (1D array)
        target_lats: Target latitudes (1D array)
        target_lons: Target longitudes (1D array)
    
    Returns:
        Regridded 2D array (target_height, target_width)
    """
    # Create interpolator
    f = interpolate.RegularGridInterpolator(
        (source_lats, source_lons),
        data_2d,
        method='linear',
        bounds_error=False,
        fill_value=None  # Use nearest for extrapolation
    )
    
    # Create target grid
    lon_grid, lat_grid = np.meshgrid(target_lons, target_lats)
    points = np.column_stack([lat_grid.ravel(), lon_grid.ravel()])
    
    # Interpolate
    regridded = f(points).reshape(len(target_lats), len(target_lons))
    
    return regridded


def convert_heat_flux(accumulated_flux, year, month):
    """
    Convert accumulated heat flux (J/m²) to average rate (W/m²).
    
    Args:
        accumulated_flux: Monthly accumulated flux in J/m²
        year: Year
        month: Month (1-12)
    
    Returns:
        Average flux in W/m²
    """
    # Calculate seconds in the month
    num_days = calendar.monthrange(year, month)[1]
    seconds_in_month = num_days * 24 * 3600
    
    # Convert J/m² to W/m² (J/m² / seconds = W/m²)
    avg_flux = accumulated_flux / seconds_in_month
    
    return avg_flux


def process_month_geotiff(
    geotiff_path,
    year,
    month,
    h5_output_dir,
    split,
    target_lats,
    target_lons,
    dry_run=False
):
    """
    Process one month of ERA5-Land GeoTIFF data.
    
    Args:
        geotiff_path: Path to GeoTIFF file (era5_land_YYYY_MM.tif)
        year: Year
        month: Month (1-12)
        h5_output_dir: Root directory for HDF5 files
        split: Data split ('train', 'val', or 'test')
        target_lats: Target latitude grid
        target_lons: Target longitude grid
        dry_run: If True, only print what would be done
    """
    
    # Read GeoTIFF file
    with rasterio.open(geotiff_path) as src:
        # Extract source coordinates
        source_lats, source_lons = extract_coordinates_from_geotiff(src)
        
        # Read all 6 bands
        bands_data = {}
        for band_idx in range(1, 7):
            band_name = BAND_MAPPING[band_idx]
            band_data = src.read(band_idx)
            bands_data[band_name] = band_data
    
    # Process each variable
    processed_vars = {}
    
    for var_name, source_data in bands_data.items():
        # Apply heat flux conversion if needed
        if var_name in FLUX_VARIABLES:
            data = convert_heat_flux(source_data, year, month)
        else:
            data = source_data.copy()
        
        # Regrid to IndiaWeatherBench grid
        regridded = regrid_bilinear(
            data,
            source_lats,
            source_lons,
            target_lats,
            target_lons
        )
        
        # Convert to float32
        processed_vars[var_name] = regridded.astype(np.float32)
    
    # Generate all 6-hourly timestamps for this month
    num_days = calendar.monthrange(year, month)[1]
    timestamps = []
    
    for day in range(1, num_days + 1):
        for hour in [0, 6, 12, 18]:
            timestamps.append((year, month, day, hour))
    
    # Write to HDF5 files (replicate monthly mean to all timesteps)
    updated_files = []
    skipped_files = []
    
    for year_ts, month_ts, day_ts, hour_ts in timestamps:
        # Construct H5 filename matching IndiaWeatherBench convention
        hour_idx = hour_ts // 6
        h5_filename = f"{year_ts:04d}-{month_ts:02d}-{day_ts:02d}_{hour_idx:02d}.h5"
        h5_path = os.path.join(h5_output_dir, split, h5_filename)
        
        if not os.path.exists(h5_path):
            skipped_files.append(h5_filename)
            continue
        
        if dry_run:
            print(f"  Would update: {h5_filename}")
            continue
        
        # Update HDF5 file (append new variables)
        try:
            with h5py.File(h5_path, 'a') as h5f:
                for var_name, var_data in processed_vars.items():
                    if var_name in h5f:
                        # Variable exists, overwrite
                        del h5f[var_name]
                    
                    # Create new dataset
                    h5f.create_dataset(
                        var_name,
                        data=var_data,
                        dtype=np.float32,
                        compression=None  # Match existing convention
                    )
            updated_files.append(h5_filename)
        
        except Exception as e:
            print(f"    Error updating {h5_filename}: {e}")
            skipped_files.append(h5_filename)
    
    return {
        'updated': len(updated_files),
        'skipped': len(skipped_files),
        'total': len(timestamps)
    }


def determine_split(year):
    """Determine which split a year belongs to."""
    if year <= 2017:
        return 'train'
    elif year == 2018:
        return 'val'
    else:  # 2019
        return 'test'


def main():
    parser = argparse.ArgumentParser(
        description='Process ERA5-Land GeoTIFF data and integrate with IndiaWeatherBench'
    )
    parser.add_argument(
        '--era5land-dir',
        type=str,
        default='/burg-archive/home/mck2199/ML-Project/data/era5_land_raw',
        help='Directory containing ERA5-Land GeoTIFF files'
    )
    parser.add_argument(
        '--h5-output-dir',
        type=str,
        default='/burg-archive/home/mck2199/ML-Project/data/indibench_h5',
        help='Root directory for IndiaWeatherBench HDF5 files'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        default=2000,
        help='Start year'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        default=2019,
        help='End year'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print what would be done without actually modifying files'
    )
    parser.add_argument(
        '--test-month',
        type=str,
        help='Test single month (format: YYYY-MM)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("ERA5-Land GeoTIFF Processing for IndiaWeatherBench Integration")
    print("=" * 80)
    print(f"Input directory:  {args.era5land_dir}")
    print(f"Output directory: {args.h5_output_dir}")
    print(f"Years:            {args.start_year} - {args.end_year}")
    print(f"Dry run:          {args.dry_run}")
    print("=" * 80)
    print()
    
    # Create target grid
    target_lats, target_lons = create_iwb_grid()
    print(f"Target Grid:")
    print(f"  Size: {len(target_lats)} × {len(target_lons)}")
    print(f"  Latitude:  {target_lats[0]:.4f}°N to {target_lats[-1]:.4f}°N")
    print(f"  Longitude: {target_lons[0]:.4f}°E to {target_lons[-1]:.4f}°E")
    print(f"  Resolution: ~0.12°")
    print()
    
    print("Variables to Process:")
    for band_idx, var_name in BAND_MAPPING.items():
        conversion = " (accumulated J/m² → W/m²)" if var_name in FLUX_VARIABLES else ""
        print(f"  Band {band_idx}: {var_name}{conversion}")
    print()
    
    # Test single month if specified
    if args.test_month:
        year, month = map(int, args.test_month.split('-'))
        split = determine_split(year)
        geotiff_file = os.path.join(args.era5land_dir, f'era5_land_{year}_{month:02d}.tif')
        
        if not os.path.exists(geotiff_file):
            print(f"Error: File not found: {geotiff_file}")
            return 1
        
        print(f"Testing month: {year}-{month:02d} (split: {split})")
        print("=" * 80)
        
        result = process_month_geotiff(
            geotiff_file,
            year,
            month,
            args.h5_output_dir,
            split,
            target_lats,
            target_lons,
            dry_run=args.dry_run
        )
        
        print(f"\nResults:")
        print(f"  Updated:  {result['updated']} files")
        print(f"  Skipped:  {result['skipped']} files")
        print(f"  Total:    {result['total']} timesteps")
        
        return 0
    
    # Process all months
    print("Processing all months...")
    print("=" * 80)
    print()
    
    total_stats = {
        'updated': 0,
        'skipped': 0,
        'total': 0,
        'processed_months': 0,
        'failed_months': 0
    }
    
    for year in range(args.start_year, args.end_year + 1):
        split = determine_split(year)
        
        for month in range(1, 13):
            geotiff_file = os.path.join(
                args.era5land_dir,
                f'era5_land_{year}_{month:02d}.tif'
            )
            
            if not os.path.exists(geotiff_file):
                print(f"✗ {year}-{month:02d}: File not found")
                total_stats['failed_months'] += 1
                continue
            
            try:
                result = process_month_geotiff(
                    geotiff_file,
                    year,
                    month,
                    args.h5_output_dir,
                    split,
                    target_lats,
                    target_lons,
                    dry_run=args.dry_run
                )
                
                total_stats['updated'] += result['updated']
                total_stats['skipped'] += result['skipped']
                total_stats['total'] += result['total']
                total_stats['processed_months'] += 1
                
                status = "✓" if result['skipped'] == 0 else "⚠"
                print(f"{status} {year}-{month:02d} ({split}): "
                      f"Updated {result['updated']}/{result['total']} files")
                
            except Exception as e:
                print(f"✗ {year}-{month:02d}: ERROR - {e}")
                total_stats['failed_months'] += 1
                import traceback
                traceback.print_exc()
    
    print()
    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Months processed:     {total_stats['processed_months']}")
    print(f"Months failed:        {total_stats['failed_months']}")
    print(f"Total timesteps:      {total_stats['total']}")
    print(f"Files updated:        {total_stats['updated']}")
    print(f"Files skipped:        {total_stats['skipped']}")
    
    if args.dry_run:
        print()
        print("⚠️  This was a DRY RUN - no files were actually modified")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

