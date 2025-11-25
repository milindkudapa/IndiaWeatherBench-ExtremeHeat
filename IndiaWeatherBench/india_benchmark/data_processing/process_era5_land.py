#!/usr/bin/env python3
"""
Process ERA5-Land data to match IndiaWeatherBench specifications.

This script:
1. Loads ERA5-Land NetCDF files
2. Regrids from 0.1° to 0.12° resolution using bilinear interpolation
3. Crops to exact IndiaWeatherBench domain (6°N-36.72°N, 66.6°E-97.25°E)
4. Temporally aggregates hourly data to 6-hourly (00, 06, 12, 18 UTC)
5. Adds variables to existing HDF5 files (or creates new ones if needed)

Variables processed:
- swvl1, swvl2: Instantaneous values at 6-hourly intervals
- slhf, sshf: Mean over 6-hour windows
- lai_hv, lai_lv: Instantaneous values at 6-hourly intervals
"""

import os
import argparse
import numpy as np
import xarray as xr
import h5py
from scipy import interpolate
from datetime import datetime, timedelta
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import json


# IndiaWeatherBench domain specifications
IWB_LAT_START = 6.0
IWB_LAT_END = 36.72
IWB_LON_START = 66.6
IWB_LON_END = 97.25
IWB_GRID_SIZE = 256


def create_iwb_grid():
    """Create the target IndiaWeatherBench grid."""
    lats = np.linspace(IWB_LAT_START, IWB_LAT_END, IWB_GRID_SIZE)
    lons = np.linspace(IWB_LON_START, IWB_LON_END, IWB_GRID_SIZE)
    return lats, lons


def regrid_era5land_to_iwb(data_2d, source_lats, source_lons, target_lats, target_lons):
    """
    Regrid ERA5-Land data (0.1°) to IndiaWeatherBench grid (0.12°).
    
    Args:
        data_2d: 2D array of data (lat, lon)
        source_lats: Source latitudes
        source_lons: Source longitudes
        target_lats: Target latitudes
        target_lons: Target longitudes
    
    Returns:
        Regridded 2D array (256, 256)
    """
    # Create interpolator
    f = interpolate.RegularGridInterpolator(
        (source_lats, source_lons),
        data_2d,
        method='linear',
        bounds_error=False,
        fill_value=np.nan
    )
    
    # Create target grid
    lon_grid, lat_grid = np.meshgrid(target_lons, target_lats)
    points = np.column_stack([lat_grid.ravel(), lon_grid.ravel()])
    
    # Interpolate
    regridded = f(points).reshape(len(target_lats), len(target_lons))
    
    return regridded


def process_era5land_file(
    era5land_nc_path,
    h5_output_dir,
    split,
    target_lats,
    target_lons,
    flux_variables=['slhf', 'sshf'],
    instant_variables=['swvl1', 'swvl2', 'lai_hv', 'lai_lv']
):
    """
    Process a single ERA5-Land NetCDF file for one year.
    
    Args:
        era5land_nc_path: Path to ERA5-Land NetCDF file
        h5_output_dir: Directory containing existing HDF5 files
        split: Data split ('train', 'val', or 'test')
        target_lats: Target latitude grid
        target_lons: Target longitude grid
        flux_variables: Variables to average over 6-hour windows
        instant_variables: Variables to sample at 6-hourly intervals
    """
    print(f"Processing: {era5land_nc_path}")
    
    # Load ERA5-Land data
    ds = xr.open_dataset(era5land_nc_path)
    
    # Get coordinates
    source_lats = ds['latitude'].values
    source_lons = ds['longitude'].values
    
    # Map variable names (ERA5-Land uses different names)
    var_mapping = {
        'swvl1': 'swvl1',
        'swvl2': 'swvl2',
        'slhf': 'slhf',
        'sshf': 'sshf',
        'lai_hv': 'lai_hv',
        'lai_lv': 'lai_lv'
    }
    
    # Check what variables are actually in the dataset
    available_vars = {}
    for short_name, long_name in var_mapping.items():
        # ERA5-Land might use different naming conventions
        possible_names = [
            long_name,
            short_name,
            f'var{short_name}',  # Sometimes uses var codes
        ]
        for name in possible_names:
            if name in ds.variables:
                available_vars[short_name] = name
                break
    
    print(f"Available variables: {list(available_vars.keys())}")
    
    # Process each 6-hourly timestamp
    times = ds['time'].values
    
    # Group times by 6-hourly intervals (00, 06, 12, 18 UTC)
    for target_hour in [0, 6, 12, 18]:
        # Find all timestamps for this hour
        target_times = [
            t for t in times
            if pd.Timestamp(t).hour == target_hour
        ]
        
        for target_time in tqdm(target_times, desc=f"Processing {target_hour:02d}Z times"):
            timestamp = pd.Timestamp(target_time)
            date_str = timestamp.strftime('%Y-%m-%d')
            hour_idx = timestamp.hour // 6
            
            # Construct H5 filename matching IndiaWeatherBench convention
            h5_filename = f"{date_str}_{hour_idx:02d}.h5"
            h5_path = os.path.join(h5_output_dir, split, h5_filename)
            
            # Check if H5 file exists
            if not os.path.exists(h5_path):
                print(f"Warning: H5 file not found: {h5_path}")
                print("Creating new H5 file (this should only happen for test purposes)")
                os.makedirs(os.path.dirname(h5_path), exist_ok=True)
            
            # Process each variable
            processed_data = {}
            
            for var_short_name in available_vars.keys():
                var_long_name = available_vars[var_short_name]
                
                if var_short_name in instant_variables:
                    # Use instantaneous value at target time
                    data = ds[var_long_name].sel(time=target_time).values
                    
                elif var_short_name in flux_variables:
                    # Average over 6-hour window centered on target time
                    # For fluxes, we want the average from (target_time - 6h) to target_time
                    start_time = timestamp - timedelta(hours=6)
                    end_time = timestamp
                    
                    # Select time window
                    time_slice = ds[var_long_name].sel(
                        time=slice(start_time, end_time)
                    )
                    
                    if len(time_slice.time) > 0:
                        data = time_slice.mean(dim='time').values
                    else:
                        # Use instantaneous if no data in window
                        data = ds[var_long_name].sel(time=target_time).values
                
                # Regrid to IndiaWeatherBench grid
                regridded_data = regrid_era5land_to_iwb(
                    data,
                    source_lats,
                    source_lons,
                    target_lats,
                    target_lons
                )
                
                processed_data[var_short_name] = regridded_data.astype(np.float32)
            
            # Add to HDF5 file
            if os.path.exists(h5_path):
                # Append to existing file
                with h5py.File(h5_path, 'a') as h5f:
                    for var_name, var_data in processed_data.items():
                        if var_name in h5f:
                            print(f"  Overwriting {var_name} in {h5_filename}")
                            del h5f[var_name]
                        h5f.create_dataset(
                            var_name,
                            data=var_data,
                            dtype=np.float32,
                            compression=None
                        )
            else:
                # Create new file
                with h5py.File(h5_path, 'w') as h5f:
                    # Add timestamp
                    h5f.create_dataset(
                        'time',
                        data=timestamp.isoformat(),
                        dtype=h5py.string_dtype()
                    )
                    # Add variables
                    for var_name, var_data in processed_data.items():
                        h5f.create_dataset(
                            var_name,
                            data=var_data,
                            dtype=np.float32,
                            compression=None
                        )
    
    ds.close()
    print(f"Completed: {era5land_nc_path}")


def process_year(args_tuple):
    """Wrapper function for multiprocessing."""
    year, era5land_dir, h5_output_dir, split, target_lats, target_lons = args_tuple
    
    era5land_file = os.path.join(era5land_dir, f'era5_land_{year}.nc')
    
    if not os.path.exists(era5land_file):
        print(f"File not found: {era5land_file}")
        return f"Skipped {year} (file not found)"
    
    try:
        process_era5land_file(
            era5land_file,
            h5_output_dir,
            split,
            target_lats,
            target_lons
        )
        return f"Completed {year}"
    except Exception as e:
        print(f"Error processing {year}: {e}")
        import traceback
        traceback.print_exc()
        return f"Failed {year}: {str(e)}"


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
        description='Process ERA5-Land data and integrate with IndiaWeatherBench'
    )
    parser.add_argument(
        '--era5land-dir',
        type=str,
        default='/burg-archive/home/mck2199/ML-Project/data/era5_land_raw',
        help='Directory containing ERA5-Land NetCDF files'
    )
    parser.add_argument(
        '--h5-output-dir',
        type=str,
        default='/burg-archive/home/mck2199/ML-Project/data/indibench_h5',
        help='Directory containing IndiaWeatherBench HDF5 files'
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
        '--num-workers',
        type=int,
        default=4,
        help='Number of parallel workers'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("ERA5-Land Data Processing for IndiaWeatherBench Integration")
    print("=" * 80)
    print(f"Input directory: {args.era5land_dir}")
    print(f"Output directory: {args.h5_output_dir}")
    print(f"Years: {args.start_year} - {args.end_year}")
    print(f"Parallel workers: {args.num_workers}")
    print("=" * 80)
    print()
    
    # Create target grid
    target_lats, target_lons = create_iwb_grid()
    print(f"Target grid: {len(target_lats)} x {len(target_lons)}")
    print(f"Latitude range: {target_lats[0]:.2f}°N - {target_lats[-1]:.2f}°N")
    print(f"Longitude range: {target_lons[0]:.2f}°E - {target_lons[-1]:.2f}°E")
    print()
    
    # Prepare processing tasks
    tasks = []
    for year in range(args.start_year, args.end_year + 1):
        split = determine_split(year)
        tasks.append((
            year,
            args.era5land_dir,
            args.h5_output_dir,
            split,
            target_lats,
            target_lons
        ))
    
    # Process years (sequentially for now to avoid issues)
    # Can be parallelized later if needed
    results = []
    for task in tasks:
        result = process_year(task)
        results.append(result)
        print(result)
    
    print()
    print("=" * 80)
    print("Processing Complete!")
    print("=" * 80)
    for result in results:
        print(f"  {result}")


if __name__ == '__main__':
    import pandas as pd  # Import here to avoid issues with multiprocessing
    main()


