#!/usr/bin/env python3
"""
Download ERA5-Land data using Google Earth Engine for the IndiaWeatherBench region.

This script downloads soil moisture and land surface variables from ERA5-Land
via Google Earth Engine (much more reliable than Copernicus CDS).

Variables:
- swvl1: Volumetric soil water layer 1 (0-7 cm depth) -> volumetric_soil_water_layer_1
- swvl2: Volumetric soil water layer 2 (7-28 cm depth) -> volumetric_soil_water_layer_2
- slhf: Surface latent heat flux -> surface_latent_heat_flux
- sshf: Surface sensible heat flux -> surface_sensible_heat_flux
- lai_hv: Leaf area index, high vegetation -> leaf_area_index_high_vegetation
- lai_lv: Leaf area index, low vegetation -> leaf_area_index_low_vegetation

Spatial domain: 6°N-37°N, 66°E-98°E (India subcontinent)
Time period: 2000-01-01 to 2019-12-31
Temporal resolution: Hourly
"""

import ee
import os
import argparse
from datetime import datetime, timedelta
import time


# ERA5-Land variable mapping (our names -> GEE band names)
GEE_VARIABLE_MAPPING = {
    'swvl1': 'volumetric_soil_water_layer_1',
    'swvl2': 'volumetric_soil_water_layer_2',
    'slhf': 'surface_latent_heat_flux',
    'sshf': 'surface_sensible_heat_flux',
    'lai_hv': 'leaf_area_index_high_vegetation',
    'lai_lv': 'leaf_area_index_low_vegetation'
}


def initialize_earth_engine():
    """Initialize Google Earth Engine."""
    try:
        ee.Initialize()
        print("✓ Earth Engine initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing Earth Engine: {e}")
        print("\nYou need to authenticate first. Run:")
        print("  earthengine authenticate")
        return False


def download_era5_land_month(year, month, output_dir, variables, region):
    """
    Download ERA5-Land data for a single month using Google Earth Engine.
    
    Args:
        year (int): Year to download
        month (int): Month to download (1-12)
        output_dir (str): Output directory
        variables (list): List of variable short names
        region (ee.Geometry): Region of interest
    
    Returns:
        bool: True if successful
    """
    output_file = os.path.join(output_dir, f'era5_land_{year}_{month:02d}.nc')
    
    # Check if file already exists
    if os.path.exists(output_file):
        print(f"  {year}-{month:02d}: Already exists, skipping")
        return True
    
    try:
        # Define date range for this month
        start_date = f'{year}-{month:02d}-01'
        # Get last day of month
        if month == 12:
            end_date = f'{year + 1}-01-01'
        else:
            end_date = f'{year}-{month + 1:02d}-01'
        
        # Load ERA5-Land hourly data
        dataset = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        
        # Filter by date and region
        filtered = dataset.filterDate(start_date, end_date).filterBounds(region)
        
        # Select only the variables we need
        gee_bands = [GEE_VARIABLE_MAPPING[v] for v in variables]
        filtered = filtered.select(gee_bands)
        
        # Check if we have data
        count = filtered.size().getInfo()
        if count == 0:
            print(f"  {year}-{month:02d}: No data available")
            return False
        
        print(f"  {year}-{month:02d}: Downloading {count} timesteps...")
        
        # Export to Google Drive (then we'll download)
        # This is a two-step process with GEE
        task = ee.batch.Export.image.toDrive(
            image=filtered.toBands(),
            description=f'era5_land_{year}_{month:02d}',
            folder='era5_land_india',
            fileNamePrefix=f'era5_land_{year}_{month:02d}',
            region=region,
            scale=11132,  # ~0.1 degree in meters at equator
            crs='EPSG:4326',
            maxPixels=1e13
        )
        
        task.start()
        
        print(f"  {year}-{month:02d}: Export task started (task ID: {task.id})")
        print(f"    → Monitor at: https://code.earthengine.google.com/tasks")
        
        return True
        
    except Exception as e:
        print(f"  {year}-{month:02d}: Error - {e}")
        return False


def download_era5_land_direct(year, month, output_dir, variables, region):
    """
    Alternative: Download ERA5-Land data directly (smaller regions only).
    
    This method tries to download directly without using Drive export.
    Only works for small data volumes.
    """
    output_file = os.path.join(output_dir, f'era5_land_{year}_{month:02d}.tif')
    
    # Check if file already exists
    if os.path.exists(output_file):
        print(f"  {year}-{month:02d}: Already exists, skipping")
        return True
    
    try:
        # Define date range for this month
        start_date = f'{year}-{month:02d}-01'
        if month == 12:
            end_date = f'{year + 1}-01-01'
        else:
            end_date = f'{year}-{month + 1:02d}-01'
        
        # Load ERA5-Land hourly data
        dataset = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        
        # Filter by date and region
        filtered = dataset.filterDate(start_date, end_date).filterBounds(region)
        
        # Select only the variables we need
        gee_bands = [GEE_VARIABLE_MAPPING[v] for v in variables]
        filtered = filtered.select(gee_bands)
        
        # Get the first image as a test
        first_image = filtered.first()
        
        # Get download URL
        url = first_image.getDownloadURL({
            'region': region,
            'scale': 11132,
            'crs': 'EPSG:4326',
            'format': 'GEO_TIFF'
        })
        
        print(f"  {year}-{month:02d}: Download URL generated")
        print(f"    URL: {url}")
        
        # Note: Actual download would require additional code to fetch and save
        # This is just a skeleton - GEE batch export to Drive is more reliable
        
        return True
        
    except Exception as e:
        print(f"  {year}-{month:02d}: Error - {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Download ERA5-Land data using Google Earth Engine'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/burg-archive/home/mck2199/ML-Project/data/era5_land_raw',
        help='Output directory for downloaded files'
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
    parser.add_argument(
        '--variables',
        nargs='+',
        default=['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv'],
        help='Variables to download'
    )
    parser.add_argument(
        '--use-drive',
        action='store_true',
        default=True,
        help='Use Google Drive export (recommended)'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 80)
    print("ERA5-Land Data Download via Google Earth Engine")
    print("=" * 80)
    print(f"Time period: {args.start_year} - {args.end_year}")
    print(f"Variables: {', '.join(args.variables)}")
    print(f"Output directory: {args.output_dir}")
    print(f"Method: {'Google Drive Export' if args.use_drive else 'Direct Download'}")
    print("=" * 80)
    print()
    
    # Initialize Earth Engine
    if not initialize_earth_engine():
        return 1
    
    # Define region of interest (IndiaWeatherBench domain)
    # Slightly expanded: 6°N-37°N, 66°E-98°E
    region = ee.Geometry.Rectangle([66, 6, 98, 37])
    
    print(f"\nRegion: 6°N-37°N, 66°E-98°E (India subcontinent)")
    print()
    
    # Check if we can access ERA5-Land
    try:
        dataset = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        test = dataset.filterDate('2000-01-01', '2000-01-02').first()
        bands = test.bandNames().getInfo()
        print(f"✓ ERA5-Land dataset accessible")
        print(f"  Available bands: {len(bands)}")
        print()
    except Exception as e:
        print(f"✗ Error accessing ERA5-Land dataset: {e}")
        return 1
    
    # Download data month by month
    print("Starting downloads...")
    print("=" * 80)
    
    if args.use_drive:
        print("\n⚠️  IMPORTANT: Google Earth Engine Batch Export to Drive")
        print("=" * 80)
        print("This script will queue export tasks to your Google Drive.")
        print("You'll need to:")
        print("  1. Monitor tasks at: https://code.earthengine.google.com/tasks")
        print("  2. Manually download files from Google Drive folder 'era5_land_india'")
        print("  3. Move downloaded files to:", args.output_dir)
        print()
        print("Alternative: Use a different download method (see documentation)")
        print("=" * 80)
        print()
    
    successful = 0
    failed = []
    
    for year in range(args.start_year, args.end_year + 1):
        print(f"\nYear {year}")
        print("-" * 40)
        
        for month in range(1, 13):
            if args.use_drive:
                success = download_era5_land_month(
                    year, month, args.output_dir, args.variables, region
                )
            else:
                success = download_era5_land_direct(
                    year, month, args.output_dir, args.variables, region
                )
            
            if success:
                successful += 1
            else:
                failed.append(f"{year}-{month:02d}")
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.5)
    
    print()
    print("=" * 80)
    print("Export Summary")
    print("=" * 80)
    print(f"Total months: {(args.end_year - args.start_year + 1) * 12}")
    print(f"Tasks queued: {successful}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed exports:")
        for item in failed:
            print(f"  - {item}")
    
    print()
    print("=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print("1. Monitor export tasks at: https://code.earthengine.google.com/tasks")
    print("2. Download completed files from Google Drive")
    print("3. Move files to:", args.output_dir)
    print("4. Run preprocessing script")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

