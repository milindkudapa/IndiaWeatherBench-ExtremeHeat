#!/usr/bin/env python3
"""
Download ERA5-Land data using Google Earth Engine with geemap.

This is an improved version that uses geemap for more reliable downloads.
Downloads month-by-month to avoid memory limits.
"""

import ee
import geemap
import os
import argparse
from datetime import datetime
import time
from tqdm import tqdm


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
    """Initialize Google Earth Engine."""
    try:
        ee.Initialize()
        print("✓ Earth Engine initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Error initializing Earth Engine: {e}")
        print("\n⚠️  You need to authenticate first:")
        print("    earthengine authenticate")
        return False


def download_era5_land_month_geemap(year, month, output_dir, variables, bbox):
    """
    Download ERA5-Land data for a single month using geemap.
    
    Args:
        year (int): Year
        month (int): Month (1-12)
        output_dir (str): Output directory
        variables (list): List of variable short names
        bbox (list): [west, south, east, north]
    """
    output_file = os.path.join(output_dir, f'era5_land_{year}_{month:02d}.tif')
    
    # Check if already exists
    if os.path.exists(output_file):
        return f"✓ {year}-{month:02d} (exists)"
    
    try:
        # Define date range
        start_date = f'{year}-{month:02d}-01'
        if month == 12:
            end_date = f'{year+1}-01-01'
        else:
            end_date = f'{year}-{month+1:02d}-01'
        
        # Load ERA5-Land
        dataset = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
        
        # Filter
        filtered = (dataset
                   .filterDate(start_date, end_date)
                   .filterBounds(ee.Geometry.Rectangle(bbox)))
        
        # Select variables
        gee_bands = [GEE_VARIABLE_MAPPING[v] for v in variables]
        filtered = filtered.select(gee_bands)
        
        # Check count
        count = filtered.size().getInfo()
        if count == 0:
            return f"✗ {year}-{month:02d} (no data)"
        
        # For geemap, we need to reduce the ImageCollection to a single image
        # We'll save all timesteps as separate bands (band per hour)
        # This creates: var_1, var_2, var_3... for each hour
        
        # Alternative: Save mean for the month (simpler)
        monthly_mean = filtered.mean()
        
        # Define region
        region = ee.Geometry.Rectangle(bbox)
        
        # Download using geemap
        geemap.ee_export_image(
            monthly_mean,
            filename=output_file,
            scale=11132,  # ~0.1 degree
            region=region,
            file_per_band=False
        )
        
        return f"✓ {year}-{month:02d} (downloaded)"
        
    except Exception as e:
        return f"✗ {year}-{month:02d} (error: {str(e)[:50]})"


def main():
    parser = argparse.ArgumentParser(
        description='Download ERA5-Land via Google Earth Engine (geemap version)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/burg-archive/home/mck2199/ML-Project/data/era5_land_raw',
        help='Output directory'
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
        '--variables',
        nargs='+',
        default=['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv'],
        help='Variables to download'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode - only download one month'
    )
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 80)
    print("ERA5-Land Download via Google Earth Engine (geemap)")
    print("=" * 80)
    print(f"Time period: {args.start_year}-{args.end_year}")
    print(f"Variables: {', '.join(args.variables)}")
    print(f"Output: {args.output_dir}")
    if args.test:
        print("⚠️  TEST MODE - Will only download one month")
    print("=" * 80)
    print()
    
    # Initialize
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
    
    # Download month by month
    print("Starting downloads...")
    print("=" * 80)
    
    results = []
    
    if args.test:
        # Test mode - just download one month
        result = download_era5_land_month_geemap(
            2000, 1, args.output_dir, args.variables, bbox
        )
        print(result)
        results.append(result)
    else:
        # Full download
        for year in range(args.start_year, args.end_year + 1):
            print(f"\nYear {year}")
            print("-" * 40)
            
            for month in tqdm(range(1, 13), desc=f"Year {year}"):
                result = download_era5_land_month_geemap(
                    year, month, args.output_dir, args.variables, bbox
                )
                results.append(result)
                
                # Print if error
                if "error" in result or "no data" in result:
                    tqdm.write(f"  {result}")
                
                # Small delay
                time.sleep(0.5)
    
    # Summary
    print()
    print("=" * 80)
    print("Download Summary")
    print("=" * 80)
    
    successful = sum(1 for r in results if "✓" in r and "exists" not in r)
    existed = sum(1 for r in results if "exists" in r)
    failed = sum(1 for r in results if "✗" in r)
    
    print(f"Total months attempted: {len(results)}")
    print(f"Downloaded: {successful}")
    print(f"Already existed: {existed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nFailed downloads:")
        for r in results:
            if "✗" in r:
                print(f"  {r}")
    
    print()
    print("=" * 80)
    print("✓ Download complete!")
    print(f"Files saved to: {args.output_dir}")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

