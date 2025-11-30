#!/usr/bin/env python3
"""
Download hourly ERA5-Land data at 6-hourly intervals (00, 06, 12, 18 UTC).

This script downloads ERA5-Land data using Copernicus CDS API, requesting
only the specific 6-hourly timestamps needed to match IndiaWeatherBench.

Strategy:
- Download data month-by-month to avoid API limits
- Request only 00, 06, 12, 18 UTC timesteps
- Save as NetCDF format for easier processing
- One file per month containing all 6-hourly timesteps
"""

import cdsapi
import os
import argparse
from datetime import datetime
import calendar


# ERA5-Land variable mapping
CDS_VARIABLE_MAPPING = {
    'swvl1': 'volumetric_soil_water_layer_1',
    'swvl2': 'volumetric_soil_water_layer_2',
    'slhf': 'surface_latent_heat_flux',
    'sshf': 'surface_sensible_heat_flux',
    'lai_hv': 'leaf_area_index_high_vegetation',
    'lai_lv': 'leaf_area_index_low_vegetation'
}


def download_month_hourly(year, month, output_dir, variables, area):
    """
    Download ERA5-Land hourly data for one month at 6-hourly intervals.
    
    Args:
        year (int): Year
        month (int): Month (1-12)
        output_dir (str): Output directory
        variables (list): List of variable short names
        area (list): [north, west, south, east]
    
    Returns:
        str: Status message
    """
    output_file = os.path.join(output_dir, f'era5_land_hourly_{year}_{month:02d}.nc')
    
    # Check if already exists
    if os.path.exists(output_file):
        print(f"  ✓ {year}-{month:02d} already exists, skipping")
        return f"✓ {year}-{month:02d} (exists)"
    
    # Convert variable names to CDS format
    cds_variables = [CDS_VARIABLE_MAPPING[v] for v in variables]
    
    # Get number of days in month
    num_days = calendar.monthrange(year, month)[1]
    
    try:
        # Initialize CDS API client
        c = cdsapi.Client()
        
        print(f"  Downloading {year}-{month:02d}...")
        print(f"    Variables: {', '.join(variables)}")
        print(f"    Days: {num_days}")
        print(f"    Times: 00:00, 06:00, 12:00, 18:00 UTC")
        
        # Make request
        c.retrieve(
            'reanalysis-era5-land',
            {
                'variable': cds_variables,
                'year': str(year),
                'month': f'{month:02d}',
                'day': [f'{i:02d}' for i in range(1, num_days + 1)],
                'time': ['00:00', '06:00', '12:00', '18:00'],  # Only 6-hourly
                'area': area,  # [north, west, south, east]
                'format': 'netcdf',
            },
            output_file
        )
        
        # Check file size
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"  ✓ {year}-{month:02d} downloaded ({file_size_mb:.1f} MB)")
        
        return f"✓ {year}-{month:02d} ({file_size_mb:.1f} MB)"
    
    except Exception as e:
        # Remove partial file if it exists
        if os.path.exists(output_file):
            os.remove(output_file)
        
        error_msg = str(e)
        print(f"  ✗ {year}-{month:02d} failed: {error_msg[:100]}")
        return f"✗ {year}-{month:02d} (error: {error_msg[:50]})"


def main():
    parser = argparse.ArgumentParser(
        description='Download hourly ERA5-Land data at 6-hourly intervals via CDS API'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/burg-archive/home/mck2199/ML-Project/data/era5_land_hourly',
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
        help='Test mode - download only one month'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 80)
    print("ERA5-Land Hourly Data Download (6-hourly timestamps)")
    print("=" * 80)
    print(f"Output directory: {args.output_dir}")
    print(f"Years: {args.start_year} - {args.end_year}")
    print(f"Variables: {', '.join(args.variables)}")
    print(f"Times: 00:00, 06:00, 12:00, 18:00 UTC (4 per day)")
    if args.test:
        print("⚠️  TEST MODE - Will only download one month (2000-01)")
    print("=" * 80)
    print()
    
    # Define area [north, west, south, east]
    # IndiaWeatherBench domain with buffer for interpolation
    area = [38, 66, 6, 98]
    print(f"Region: {area} (North, West, South, East)")
    print()
    
    # Download month by month
    results = []
    total_months = 0
    
    if args.test:
        # Test mode - download just January 2000
        result = download_month_hourly(2000, 1, args.output_dir, args.variables, area)
        results.append(result)
        total_months = 1
    else:
        # Download all months
        for year in range(args.start_year, args.end_year + 1):
            print(f"\n{'=' * 80}")
            print(f"Year {year}")
            print(f"{'=' * 80}")
            
            for month in range(1, 13):
                result = download_month_hourly(year, month, args.output_dir, args.variables, area)
                results.append(result)
                total_months += 1
    
    # Summary
    print()
    print("=" * 80)
    print("DOWNLOAD SUMMARY")
    print("=" * 80)
    
    successful = sum(1 for r in results if r.startswith('✓'))
    failed = sum(1 for r in results if r.startswith('✗'))
    
    print(f"Total months: {total_months}")
    print(f"Successful:   {successful}")
    print(f"Failed:       {failed}")
    print()
    
    if failed > 0:
        print("Failed months:")
        for r in results:
            if r.startswith('✗'):
                print(f"  {r}")
    
    print("=" * 80)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())

