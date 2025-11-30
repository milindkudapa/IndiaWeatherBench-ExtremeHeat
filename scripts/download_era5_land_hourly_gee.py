#!/usr/bin/env python3
"""
Download hourly ERA5-Land data at 6-hourly intervals using Google Earth Engine.

This script downloads ERA5-Land hourly data at specific times (00, 06, 12, 18 UTC)
to match IndiaWeatherBench temporal resolution.

Strategy:
- Use Google Earth Engine batch export to Drive
- Download day-by-day to avoid memory limits
- Export only 00, 06, 12, 18 UTC timesteps
- Save as GeoTIFF (one file per day with 4 bands for each variable)
"""

import ee
import os
import argparse
import time
from datetime import datetime, timedelta
import calendar


# ERA5-Land variable mapping
GEE_VARIABLE_MAPPING = {
    'swvl1': 'volumetric_soil_water_layer_1',
    'swvl2': 'volumetric_soil_water_layer_2',
    'slhf': 'surface_latent_heat_flux',
    'sshf': 'surface_sensible_heat_flux',
    'lai_hv': 'leaf_area_index_high_vegetation',
    'lai_lv': 'leaf_area_index_low_vegetation'
}


def initialize_earth_engine():
    """Initialize Earth Engine."""
    try:
        ee.Initialize()
        print("✓ Earth Engine initialized")
        return True
    except Exception as e:
        print(f"✗ Earth Engine initialization failed: {e}")
        print("\nPlease authenticate first:")
        print("  python scripts/authenticate_gee.py")
        return False


def export_day_to_drive(year, month, day, variables, bbox, folder='era5_land_gee'):
    """
    Export one day of ERA5-Land data (4 timesteps: 00, 06, 12, 18 UTC) to Google Drive.
    
    Args:
        year (int): Year
        month (int): Month (1-12)
        day (int): Day of month
        variables (list): List of variable short names
        bbox (list): [west, south, east, north]
        folder (str): Google Drive folder name
    
    Returns:
        ee.batch.Task: Export task
    """
    # Define date for this day
    date_str = f'{year}-{month:02d}-{day:02d}'
    
    # Create image collection for this day at 6-hourly intervals
    dataset = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
    
    # Filter for specific hours (00, 06, 12, 18 UTC)
    hours_to_get = [0, 6, 12, 18]
    
    # Get images for each hour
    images = []
    for hour in hours_to_get:
        timestamp = f'{year}-{month:02d}-{day:02d}T{hour:02d}:00:00'
        
        # Filter to exact timestamp
        img = dataset.filterDate(
            timestamp,
            ee.Date(timestamp).advance(1, 'hour')
        ).first()
        
        # Select variables
        gee_bands = [GEE_VARIABLE_MAPPING[v] for v in variables]
        img = img.select(gee_bands)
        
        # Rename bands to include hour (e.g., swvl1_00, swvl1_06, etc.)
        new_names = [f'{v}_{hour:02d}' for v in variables]
        img = img.rename(new_names)
        
        images.append(img)
    
    # Combine all 4 timesteps into one image with multiple bands
    # This creates bands like: swvl1_00, swvl1_06, swvl1_12, swvl1_18, swvl2_00, etc.
    combined = images[0]
    for img in images[1:]:
        combined = combined.addBands(img)
    
    # Define region
    region = ee.Geometry.Rectangle(bbox)
    
    # Export to Drive
    task = ee.batch.Export.image.toDrive(
        image=combined,
        description=f'era5_land_{year}_{month:02d}_{day:02d}',
        folder=folder,
        fileNamePrefix=f'era5_land_{year}_{month:02d}_{day:02d}',
        region=region,
        scale=11132,  # ~0.1 degree
        crs='EPSG:4326',
        fileFormat='GeoTIFF',
        maxPixels=1e13
    )
    
    return task


def main():
    parser = argparse.ArgumentParser(
        description='Download hourly ERA5-Land at 6-hourly intervals via Google Earth Engine'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/burg-archive/home/mck2199/ML-Project/data/era5_land_hourly',
        help='Local output directory (for tracking)'
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
        '--start-month',
        type=int,
        default=1,
        help='Start month (1-12)'
    )
    parser.add_argument(
        '--end-month',
        type=int,
        default=12,
        help='End month (1-12)'
    )
    parser.add_argument(
        '--variables',
        nargs='+',
        default=['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv'],
        help='Variables to download'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode - export only first week of January 2000'
    )
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=50,
        help='Maximum concurrent export tasks'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("ERA5-Land Hourly Download via Google Earth Engine")
    print("=" * 80)
    print(f"Years: {args.start_year} - {args.end_year}")
    print(f"Variables: {', '.join(args.variables)}")
    print(f"Times per day: 00, 06, 12, 18 UTC (4 timesteps)")
    print(f"Max concurrent tasks: {args.max_concurrent}")
    if args.test:
        print("⚠️  TEST MODE - Will only export first week of January 2000")
    print("=" * 80)
    print()
    
    # Initialize Earth Engine
    if not initialize_earth_engine():
        return 1
    
    # Define bbox [west, south, east, north]
    bbox = [66, 6, 98, 37]
    print(f"Region: {bbox} (6°N-37°N, 66°E-98°E)")
    print()
    
    # Test ERA5-Land access
    try:
        dataset = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        test = dataset.filterDate('2000-01-01', '2000-01-02').first()
        print("✓ ERA5-Land dataset accessible")
        print()
    except Exception as e:
        print(f"✗ Cannot access ERA5-Land: {e}")
        return 1
    
    # Queue export tasks
    print("Queuing export tasks to Google Drive...")
    print("=" * 80)
    print()
    
    tasks = []
    
    if args.test:
        # Test mode - only first week of January 2000
        year, month = 2000, 1
        for day in range(1, 8):  # Days 1-7
            print(f"  Queuing: {year}-{month:02d}-{day:02d}")
            task = export_day_to_drive(year, month, day, args.variables, bbox)
            task.start()
            tasks.append((year, month, day, task))
            time.sleep(0.5)
    else:
        # Full download
        for year in range(args.start_year, args.end_year + 1):
            # Determine month range for this year
            if year == args.start_year:
                start_m = args.start_month
            else:
                start_m = 1
            
            if year == args.end_year:
                end_m = args.end_month
            else:
                end_m = 12
            
            for month in range(start_m, end_m + 1):
                num_days = calendar.monthrange(year, month)[1]
                
                print(f"\nYear {year}, Month {month:02d} ({num_days} days)")
                
                for day in range(1, num_days + 1):
                    print(f"  Queuing: {year}-{month:02d}-{day:02d}")
                    
                    try:
                        task = export_day_to_drive(year, month, day, args.variables, bbox)
                        task.start()
                        tasks.append((year, month, day, task))
                        time.sleep(0.5)  # Small delay between requests
                        
                        # Check if we've hit max concurrent tasks
                        if len(tasks) % args.max_concurrent == 0:
                            print(f"\n  ⏸️  Reached {args.max_concurrent} tasks, waiting for some to complete...")
                            # Wait for some tasks to complete
                            time.sleep(60)
                    
                    except Exception as e:
                        print(f"    ✗ Failed to queue {year}-{month:02d}-{day:02d}: {e}")
    
    print()
    print("=" * 80)
    print(f"✓ Queued {len(tasks)} export tasks to Google Drive")
    print("=" * 80)
    print()
    print("IMPORTANT: Next steps")
    print("─" * 80)
    print("1. Monitor tasks at: https://code.earthengine.google.com/tasks")
    print()
    print("2. Tasks will export to Google Drive folder: 'era5_land_hourly'")
    print()
    print("3. After tasks complete, download files from Google Drive:")
    print("   - Files will be named: era5_land_YYYY_MM_DD.tif")
    print("   - Each file has 24 bands (6 variables × 4 timesteps)")
    print(f"   - Total files: {len(tasks)}")
    print()
    print("4. Move downloaded files to:")
    print(f"   {args.output_dir}")
    print()
    print("5. Then run the preprocessing script to integrate with HDF5 files")
    print()
    
    # Create a summary file
    summary_file = os.path.join(args.output_dir, 'export_summary.txt')
    os.makedirs(args.output_dir, exist_ok=True)
    
    with open(summary_file, 'w') as f:
        f.write(f"ERA5-Land Hourly Export Summary\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"\n")
        f.write(f"Total tasks queued: {len(tasks)}\n")
        f.write(f"Variables: {', '.join(args.variables)}\n")
        f.write(f"Times per day: 00, 06, 12, 18 UTC\n")
        f.write(f"\n")
        f.write(f"Task list:\n")
        for year, month, day, task in tasks:
            f.write(f"  {year}-{month:02d}-{day:02d} (Task ID: {task.id})\n")
    
    print(f"Summary saved to: {summary_file}")
    print()
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

