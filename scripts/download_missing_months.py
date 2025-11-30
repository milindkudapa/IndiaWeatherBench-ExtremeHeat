#!/usr/bin/env python3
"""
Download only the missing ERA5-Land months.

This script identifies which months are missing and attempts to download them
using Earth Engine batch export to Drive (more reliable for large requests).
"""

import ee
import os
import time


# ERA5-Land variable mapping
GEE_VARIABLE_MAPPING = {
    'swvl1': 'volumetric_soil_water_layer_1',
    'swvl2': 'volumetric_soil_water_layer_2',
    'slhf': 'surface_latent_heat_flux',
    'sshf': 'surface_sensible_heat_flux',
    'lai_hv': 'leaf_area_index_high_vegetation',
    'lai_lv': 'leaf_area_index_low_vegetation'
}


def find_missing_months(data_dir, start_year=2000, end_year=2019):
    """Find which months are missing."""
    missing = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            filename = f'era5_land_{year}_{month:02d}.tif'
            if not os.path.exists(os.path.join(data_dir, filename)):
                missing.append((year, month))
    return missing


def export_month_to_drive(year, month, variables, bbox):
    """
    Export a month of ERA5-Land data to Google Drive using batch export.
    
    This is more reliable than direct download for large requests.
    """
    # Define date range
    start_date = f'{year}-{month:02d}-01'
    if month == 12:
        end_date = f'{year+1}-01-01'
    else:
        end_date = f'{year}-{month+1:02d}-01'
    
    # Load data
    dataset = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
    filtered = dataset.filterDate(start_date, end_date).filterBounds(
        ee.Geometry.Rectangle(bbox)
    )
    
    # Select variables
    gee_bands = [GEE_VARIABLE_MAPPING[v] for v in variables]
    filtered = filtered.select(gee_bands)
    
    # Compute monthly mean (reduces size significantly)
    monthly_mean = filtered.mean()
    
    # Define region
    region = ee.Geometry.Rectangle(bbox)
    
    # Export to Drive
    task = ee.batch.Export.image.toDrive(
        image=monthly_mean,
        description=f'era5_land_{year}_{month:02d}',
        folder='era5_land_india',
        fileNamePrefix=f'era5_land_{year}_{month:02d}',
        region=region,
        scale=11132,  # ~0.1 degree
        crs='EPSG:4326',
        fileFormat='GeoTIFF',
        maxPixels=1e13
    )
    
    task.start()
    
    return task


def main():
    data_dir = '/burg-archive/home/mck2199/ML-Project/data/era5_land_raw'
    variables = ['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv']
    bbox = [66, 6, 98, 37]  # [west, south, east, north]
    
    print("=" * 80)
    print("Download Missing ERA5-Land Months via Google Drive Export")
    print("=" * 80)
    print()
    
    # Initialize Earth Engine
    try:
        ee.Initialize()
        print("✓ Earth Engine initialized")
    except Exception as e:
        print(f"✗ Error initializing Earth Engine: {e}")
        print("\nRun authentication first:")
        print("  python scripts/authenticate_gee.py")
        return 1
    
    # Find missing months
    missing = find_missing_months(data_dir)
    
    print(f"\nFound {len(missing)} missing months:")
    for year, month in missing[:10]:
        print(f"  {year}-{month:02d}")
    if len(missing) > 10:
        print(f"  ... and {len(missing) - 10} more")
    print()
    
    if len(missing) == 0:
        print("✓ All months already downloaded!")
        return 0
    
    # Confirm
    print("=" * 80)
    print("⚠️  Google Drive Batch Export Method")
    print("=" * 80)
    print("This will create export tasks in your Google Earth Engine account.")
    print("Tasks will export to Google Drive folder: 'era5_land_india'")
    print()
    print("After tasks complete, you'll need to:")
    print(f"  1. Download files from Google Drive")
    print(f"  2. Move them to: {data_dir}")
    print("=" * 80)
    print()
    
    response = input(f"Queue {len(missing)} export tasks? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Cancelled.")
        return 0
    
    # Queue export tasks
    print(f"\nQueueing {len(missing)} export tasks...")
    tasks = []
    
    for year, month in missing:
        try:
            task = export_month_to_drive(year, month, variables, bbox)
            tasks.append((year, month, task))
            print(f"  ✓ Queued: {year}-{month:02d} (task ID: {task.id})")
            time.sleep(0.5)  # Small delay between requests
        except Exception as e:
            print(f"  ✗ Failed to queue {year}-{month:02d}: {e}")
    
    print()
    print("=" * 80)
    print(f"✓ Queued {len(tasks)} export tasks")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Monitor tasks at: https://code.earthengine.google.com/tasks")
    print("  2. Wait for tasks to complete (may take several hours)")
    print("  3. Download files from Google Drive folder 'era5_land_india'")
    print(f"  4. Move files to: {data_dir}")
    print("  5. Run this script again to verify all months are present")
    print()
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

