#!/usr/bin/env python3
"""
Process ERA5-Land NetCDF data from CDS and integrate with IndiaWeatherBench HDF5 files.

This script handles all format conversions:
1. Extracts NetCDF files from ZIP archives
2. Reads 6-hourly ERA5-Land data (00, 06, 12, 18 UTC)
3. Converts heat fluxes from accumulated J/m² to average W/m²
4. Regrids from 321×321 @ 0.1° to 256×256 @ 0.12° using bilinear interpolation
5. Crops to exact IndiaWeatherBench domain
6. Integrates into existing HDF5 files (adds new variables)

Input: ZIP-compressed NetCDF files (era5_land_hourly_YYYY_MM.nc)
Output: Updated HDF5 files with 6 new variables
"""

import os
import argparse
import numpy as np
import xarray as xr
import netCDF4
import h5py
import zipfile
from scipy import interpolate
from datetime import datetime, timedelta
from tqdm import tqdm
import pandas as pd
import warnings
import tempfile
import shutil

warnings.filterwarnings('ignore')


# IndiaWeatherBench domain specifications
IWB_LAT_START = 6.0
IWB_LAT_END = 36.72
IWB_LON_START = 66.6
IWB_LON_END = 97.25
IWB_GRID_SIZE = 256
IWB_HOURS_PER_DAY = [0, 6, 12, 18]  # 6-hourly UTC

# ERA5-Land variables
VARIABLES = ['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv']

# Variables that need conversion from accumulated J/m² to average W/m²
FLUX_VARIABLES = ['slhf', 'sshf']


def extract_netcdf_from_zip(zip_path, extraction_base_dir):
    """
    Extract NetCDF file from ZIP archive directly to a unique filename.
    
    Args:
        zip_path: Path to ZIP file
        extraction_base_dir: Base directory for extraction (uses scratch space)
    
    Returns:
        str: Path to extracted NetCDF file
    """
    # Create unique filename based on ZIP file and timestamp
    import uuid
    import time
    zip_basename = os.path.basename(zip_path).replace('.nc', '')
    unique_id = uuid.uuid4().hex[:8]
    extracted_filename = f'{zip_basename}_{unique_id}.nc'
    extracted_path = os.path.join(extraction_base_dir, extracted_filename)
    
    # Extract data_0.nc directly to final path
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        with zip_ref.open('data_0.nc') as source:
            with open(extracted_path, 'wb') as target:
                shutil.copyfileobj(source, target)
                # Ensure all data is written to disk
                target.flush()
                os.fsync(target.fileno())
    
    # Brief wait for filesystem to ensure file is fully accessible
    time.sleep(0.1)
    
    # Verify the extracted file exists and has correct size
    if not os.path.exists(extracted_path):
        raise FileNotFoundError(f"Extracted file not found: {extracted_path}")
    
    file_size = os.path.getsize(extracted_path)
    if file_size == 0:
        raise RuntimeError(f"Extracted file is empty: {extracted_path}")
    
    return extracted_path


def create_iwb_grid():
    """Create target IWB grid."""
    iwb_lats = np.linspace(IWB_LAT_START, IWB_LAT_END, IWB_GRID_SIZE)
    iwb_lons = np.linspace(IWB_LON_START, IWB_LON_END, IWB_GRID_SIZE)
    return iwb_lats, iwb_lons


def regrid_data(data, source_lats, source_lons, target_lats, target_lons):
    """
    Regrid data from source grid to target grid using bilinear interpolation.
    
    Args:
        data: 2D array (lat, lon) from source
        source_lats: 1D array of source latitudes
        source_lons: 1D array of source longitudes
        target_lats: 1D array of target latitudes
        target_lons: 1D array of target longitudes
    
    Returns:
        regridded: 2D array (target_lat, target_lon)
    """
    # Create interpolator
    interp_func = interpolate.RegularGridInterpolator(
        (source_lats, source_lons), 
        data,
        method='linear',
        bounds_error=False,
        fill_value=np.nan
    )
    
    # Create target grid
    target_lon_grid, target_lat_grid = np.meshgrid(target_lons, target_lats)
    target_points = np.stack([target_lat_grid.ravel(), target_lon_grid.ravel()], axis=-1)
    
    # Interpolate
    regridded = interp_func(target_points).reshape(len(target_lats), len(target_lons))
    
    return regridded


def convert_flux_units(flux_data_j_m2, hours_accumulated=6):
    """
    Convert accumulated heat flux from J/m² to average W/m².
    
    ERA5-Land heat fluxes are accumulated over the preceding hour at each timestep.
    For 6-hourly data, we have the accumulated value over that 6-hour period.
    
    Args:
        flux_data_j_m2: Flux in J/m² (accumulated over time period)
        hours_accumulated: Number of hours over which flux was accumulated
    
    Returns:
        Flux in W/m² (average rate)
    """
    seconds = hours_accumulated * 3600
    return flux_data_j_m2 / seconds


def process_era5land_netcdf(netcdf_path, h5_dir, target_lats, target_lons, year, month):
    """
    Process one month of ERA5-Land NetCDF data and integrate into HDF5 files.
    
    Args:
        netcdf_path: Path to extracted NetCDF file
        h5_dir: Directory containing IWB HDF5 files
        target_lats: Target latitude grid
        target_lons: Target longitude grid
        year: Year of data
        month: Month of data
    
    Returns:
        Number of timesteps processed
    """
    # Open ERA5-Land NetCDF using netCDF4 directly (bypasses xarray file opening issues)
    import time
    
    # Ensure file exists and is readable
    if not os.path.exists(netcdf_path):
        raise FileNotFoundError(f"NetCDF file not found: {netcdf_path}")
    
    # Brief delay to ensure filesystem has completed write
    time.sleep(0.2)
    
    # Open with netCDF4 library directly
    try:
        nc_file = netCDF4.Dataset(netcdf_path, 'r')
    except Exception as e:
        raise RuntimeError(f"Failed to open {netcdf_path} with netCDF4: {e}")
    
    # Manually extract data from netCDF4 to avoid xarray's caching issues
    try:
        # Get coordinates
        source_lats = nc_file.variables['latitude'][:]
        source_lons = nc_file.variables['longitude'][:]
        times_raw = nc_file.variables['valid_time'][:]
        
        # Convert times to pandas datetime
        time_unit = nc_file.variables['valid_time'].units
        import cftime
        if hasattr(nc_file.variables['valid_time'], 'calendar'):
            calendar = nc_file.variables['valid_time'].calendar
        else:
            calendar = 'standard'
        
        times = netCDF4.num2date(times_raw, units=time_unit, calendar=calendar)
        times = pd.to_datetime([t.strftime('%Y-%m-%d %H:%M:%S') for t in times])
        
    except Exception as e:
        nc_file.close()
        raise RuntimeError(f"Failed to read coordinates from {netcdf_path}: {e}")
    
    # Store the open file handle to read variables later
    # (keeping dataset reference to prevent premature closure)
    ds = None  # Not using xarray dataset anymore
    
    processed_count = 0
    
    try:
        for time_idx, timestamp in enumerate(times):
            # Create HDF5 filename matching IWB convention
            # IWB uses indices 0-3 for hours 00, 06, 12, 18 UTC
            hour = timestamp.hour
            if hour == 0:
                hour_idx = '00'
            elif hour == 6:
                hour_idx = '01'
            elif hour == 12:
                hour_idx = '02'
            elif hour == 18:
                hour_idx = '03'
            else:
                # Skip non-6-hourly timesteps
                continue
            
            h5_filename = f"{timestamp.strftime('%Y-%m-%d')}_{hour_idx}.h5"
            
            # IWB files are organized in train/val/test subdirectories
            # Determine which subdirectory based on year
            file_year = timestamp.year
            if file_year <= 2017:
                subdir = 'train'
            elif file_year == 2018:
                subdir = 'val'
            else:  # 2019+
                subdir = 'test'
            
            h5_path = os.path.join(h5_dir, subdir, h5_filename)
            
            if not os.path.exists(h5_path):
                # File doesn't exist, skip
                continue
            
            # Process each variable
            new_data = {}
            for var in VARIABLES:
                # Get data for this timestep from netCDF4 file
                data = nc_file.variables[var][time_idx, :, :]
                
                # Handle flux conversion (J/m² → W/m²)
                if var in FLUX_VARIABLES:
                    # ERA5-Land fluxes are accumulated over preceding hour at each timestep
                    # For 6-hourly data, convert accumulated J/m² to average W/m²
                    data = convert_flux_units(data, hours_accumulated=6)
                
                # Regrid to IWB grid
                regridded = regrid_data(data, source_lats, source_lons, target_lats, target_lons)
                
                new_data[var] = regridded.astype(np.float32)
            
            # Add variables to HDF5 file
            try:
                with h5py.File(h5_path, 'a') as h5f:
                    for var, data in new_data.items():
                        if var in h5f:
                            # Variable already exists, overwrite
                            del h5f[var]
                        
                        # Create dataset
                        h5f.create_dataset(
                            var,
                            data=data,
                            dtype=np.float32,
                            compression=None  # Match IWB convention
                        )
                
                processed_count += 1
                    
            except Exception as e:
                print(f"  Error processing {h5_filename}: {e}")
                continue
    
    finally:
        # Always close the netCDF4 file
        nc_file.close()
    
    return processed_count


def main():
    parser = argparse.ArgumentParser(
        description='Process ERA5-Land NetCDF data and integrate with IWB HDF5 files'
    )
    parser.add_argument(
        '--era5land-dir',
        type=str,
        required=True,
        help='Directory containing ERA5-Land ZIP files'
    )
    parser.add_argument(
        '--h5-output-dir',
        type=str,
        required=True,
        help='Directory containing IWB HDF5 files'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        default=2000,
        help='Start year (default: 2000)'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        default=2019,
        help='End year (default: 2019)'
    )
    
    args = parser.parse_args()
    
    # Create target grid
    print("Creating IWB target grid...")
    target_lats, target_lons = create_iwb_grid()
    print(f"  Target grid: {len(target_lats)} × {len(target_lons)}")
    print(f"  Latitude range: {target_lats[0]:.2f}° to {target_lats[-1]:.2f}°")
    print(f"  Longitude range: {target_lons[0]:.2f}° to {target_lons[-1]:.2f}°")
    
    # Process each month
    total_months = (args.end_year - args.start_year + 1) * 12
    total_processed = 0
    
    print(f"\nProcessing {total_months} months from {args.start_year} to {args.end_year}...")
    
    # Create extraction directory in project space (not /local or /tmp)
    extraction_base_dir = os.path.join(args.era5land_dir, 'temp_extracted')
    os.makedirs(extraction_base_dir, exist_ok=True)
    print(f"Extraction directory: {extraction_base_dir}")
    
    with tqdm(total=total_months, desc="Overall progress") as pbar:
        for year in range(args.start_year, args.end_year + 1):
            for month in range(1, 13):
                # Find ERA5-Land ZIP file
                zip_filename = f'era5_land_hourly_{year}_{month:02d}.nc'
                zip_path = os.path.join(args.era5land_dir, zip_filename)
                
                if not os.path.exists(zip_path):
                    print(f"\nWarning: Missing file {zip_filename}, skipping...")
                    pbar.update(1)
                    continue
                
                # Extract NetCDF to unique file in scratch space
                netcdf_path = None
                try:
                    netcdf_path = extract_netcdf_from_zip(zip_path, extraction_base_dir)
                except Exception as e:
                    print(f"\nError extracting {zip_filename}: {e}")
                    pbar.update(1)
                    continue
                
                # Process the month
                try:
                    processed_count = process_era5land_netcdf(
                        netcdf_path,
                        args.h5_output_dir,
                        target_lats,
                        target_lons,
                        year,
                        month
                    )
                    total_processed += processed_count
                    
                except Exception as e:
                    print(f"\nError processing {zip_filename}: {e}")
                
                finally:
                    # Clean up extracted file
                    if netcdf_path and os.path.exists(netcdf_path):
                        os.remove(netcdf_path)
                
                pbar.update(1)
                pbar.set_postfix({'processed': total_processed})
    
    # Clean up extraction base directory
    if os.path.exists(extraction_base_dir):
        print(f"\nCleaning up extraction directory...")
        shutil.rmtree(extraction_base_dir, ignore_errors=True)
    
    print(f"\n{'='*80}")
    print(f"Processing complete!")
    print(f"{'='*80}")
    print(f"Total timesteps processed: {total_processed}")
    print(f"Variables added per timestep: {len(VARIABLES)}")
    print(f"Total datasets created: {total_processed * len(VARIABLES)}")
    print(f"\nNext steps:")
    print(f"1. Update normalization parameters (compute_norm_params.py)")
    print(f"2. Create new config with 43 variables")
    print(f"3. Validate integration")
    print(f"4. Train expanded model")


if __name__ == '__main__':
    main()

