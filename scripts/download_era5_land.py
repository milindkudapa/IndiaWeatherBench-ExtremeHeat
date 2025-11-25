#!/usr/bin/env python3
"""
Download ERA5-Land data for the IndiaWeatherBench region.

This script downloads soil moisture and land surface variables from ERA5-Land
for the same spatial and temporal coverage as the IndiaWeatherBench dataset.

Variables:
- swvl1: Volumetric soil water layer 1 (0-7 cm depth)
- swvl2: Volumetric soil water layer 2 (7-28 cm depth)
- slhf: Surface latent heat flux
- sshf: Surface sensible heat flux
- lai_hv: Leaf area index, high vegetation
- lai_lv: Leaf area index, low vegetation

Spatial domain: 6°N-37°N, 66°E-98°E (slightly expanded for interpolation)
Time period: 2000-01-01 to 2019-12-31
Temporal resolution: Hourly (to be aggregated to 6-hourly later)
"""

import cdsapi
import os
import argparse
from datetime import datetime, timedelta


def download_era5_land_year(year, output_dir, variables, area):
    """
    Download ERA5-Land data for a single year.
    
    Args:
        year (int): Year to download
        output_dir (str): Output directory
        variables (list): List of variable names
        area (list): Bounding box [north, west, south, east]
    """
    client = cdsapi.Client()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f'era5_land_{year}.nc')
    
    # Check if file already exists
    if os.path.exists(output_file):
        print(f"File {output_file} already exists. Skipping download.")
        return
    
    print(f"Downloading ERA5-Land data for year {year}...")
    print(f"Output file: {output_file}")
    
    # Map to CDS API variable names
    cds_variable_mapping = {
        'swvl1': 'volumetric_soil_water_layer_1',
        'swvl2': 'volumetric_soil_water_layer_2',
        'slhf': 'surface_latent_heat_flux',
        'sshf': 'surface_sensible_heat_flux',
        'lai_hv': 'leaf_area_index_high_vegetation',
        'lai_lv': 'leaf_area_index_low_vegetation'
    }
    
    cds_variables = [cds_variable_mapping[v] for v in variables]
    
    # Generate all months and days for the year
    months = [f'{m:02d}' for m in range(1, 13)]
    days = [f'{d:02d}' for d in range(1, 32)]
    hours = [f'{h:02d}:00' for h in range(24)]  # All hours for hourly data
    
    try:
        client.retrieve(
            'reanalysis-era5-land',
            {
                'product_type': 'reanalysis',
                'variable': cds_variables,
                'year': str(year),
                'month': months,
                'day': days,
                'time': hours,
                'area': area,  # [North, West, South, East]
                'format': 'netcdf',
            },
            output_file
        )
        print(f"Successfully downloaded data for year {year}")
        
    except Exception as e:
        print(f"Error downloading data for year {year}: {e}")
        # Remove partial download if it exists
        if os.path.exists(output_file):
            os.remove(output_file)
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Download ERA5-Land data for IndiaWeatherBench integration'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/burg-archive/home/mck2199/ML-Project/data/era5_land_raw',
        help='Output directory for downloaded NetCDF files'
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
    
    args = parser.parse_args()
    
    # Define bounding box: [North, West, South, East]
    # Slightly expanded from IndiaWeatherBench (6°N-36.72°N, 66.6°E-97.25°E)
    # to ensure complete coverage after regridding
    area = [37, 66, 6, 98]
    
    print("=" * 80)
    print("ERA5-Land Data Download for IndiaWeatherBench Integration")
    print("=" * 80)
    print(f"Time period: {args.start_year} - {args.end_year}")
    print(f"Spatial domain: {area[0]}°N - {area[2]}°N, {area[1]}°E - {area[3]}°E")
    print(f"Variables: {', '.join(args.variables)}")
    print(f"Output directory: {args.output_dir}")
    print("=" * 80)
    print()
    
    # Download data year by year
    for year in range(args.start_year, args.end_year + 1):
        try:
            download_era5_land_year(
                year=year,
                output_dir=args.output_dir,
                variables=args.variables,
                area=area
            )
        except Exception as e:
            print(f"Failed to download year {year}. Error: {e}")
            print("You may need to retry this year later.")
            continue
    
    print()
    print("=" * 80)
    print("Download complete!")
    print(f"Downloaded files are in: {args.output_dir}")
    print("=" * 80)


if __name__ == '__main__':
    main()


