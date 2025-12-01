#!/usr/bin/env python3
"""
Compute normalization parameters for ERA5-Land variables and update norm_params.json.

This script:
1. Processes only the 6 new ERA5-Land variables
2. Computes mean, std, log_mean, log_std, diff_mean, diff_std
3. Uses training period only (2000-2017)
4. Updates existing norm_params.json with new statistics
"""

import argparse
import os
import h5py
import numpy as np
import json
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing


# ERA5-Land variables to process
ERA5_LAND_VARS = ['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv']


def get_h5_files_for_period(h5_dir, start_year=2000, end_year=2017):
    """
    Get all HDF5 files within the training period.
    
    Args:
        h5_dir: Base directory containing train/val/test subdirectories with HDF5 files
        start_year: Start year (inclusive)
        end_year: End year (inclusive)
    
    Returns:
        List of file paths
    """
    all_files = []
    
    # IWB files are organized in train/val/test subdirectories
    # Training period is in the 'train' subdirectory
    train_dir = os.path.join(h5_dir, 'train')
    
    if not os.path.exists(train_dir):
        print(f"Warning: Training directory not found: {train_dir}")
        return all_files
    
    for fname in sorted(os.listdir(train_dir)):
        if not fname.endswith('.h5'):
            continue
        
        # Parse date from filename (YYYY-MM-DD_HH.h5)
        try:
            date_str = fname.split('_')[0]  # YYYY-MM-DD
            year = int(date_str.split('-')[0])
            
            if start_year <= year <= end_year:
                all_files.append(os.path.join(train_dir, fname))
        except:
            continue
    
    return sorted(all_files)


def process_chunk(chunk_files, variables):
    """
    Process a chunk of files and compute statistics.
    
    Args:
        chunk_files: List of HDF5 file paths
        variables: List of variable names to process
    
    Returns:
        dict: Statistics for this chunk
    """
    chunk_data = {v: [] for v in variables}
    
    # Load data from all files in chunk
    for fpath in chunk_files:
        try:
            with h5py.File(fpath, 'r') as f:
                for var in variables:
                    if var in f:
                        data = f[var][:]
                        chunk_data[var].append(data)
        except Exception as e:
            print(f"  Warning: Error reading {os.path.basename(fpath)}: {e}")
            continue
    
    # Stack data (timesteps, lat, lon)
    chunk_data = {
        v: np.stack(chunk_data[v], axis=0) 
        for v in variables if len(chunk_data[v]) > 0
    }
    
    if not chunk_data:
        return None
    
    # Compute log-transformed data
    # Use small epsilon to avoid log(0)
    log_chunk_data = {
        v: np.log(1 + np.abs(chunk_data[v]) / 1e-5) 
        for v in chunk_data.keys()
    }
    
    # Compute temporal differences
    diff_data = {
        v: np.diff(chunk_data[v], axis=0) 
        for v in chunk_data.keys()
    }
    
    # Compute statistics (ignoring NaNs for ocean/masked regions)
    chunk_stats = {
        "mean": {},
        "std": {},
        "log_mean": {},
        "log_std": {},
        "diff_mean": {},
        "diff_std": {},
    }
    
    for v in chunk_data.keys():
        # Standard statistics
        chunk_stats["mean"][v] = np.nanmean(chunk_data[v])
        chunk_stats["std"][v] = np.nanstd(chunk_data[v])
        
        # Log statistics
        chunk_stats["log_mean"][v] = np.nanmean(log_chunk_data[v])
        chunk_stats["log_std"][v] = np.nanstd(log_chunk_data[v])
        
        # Diff statistics
        chunk_stats["diff_mean"][v] = np.nanmean(diff_data[v])
        chunk_stats["diff_std"][v] = np.nanstd(diff_data[v])
    
    return chunk_stats


def aggregate_statistics(all_chunk_stats, variables, chunk_size):
    """
    Aggregate statistics from all chunks into final statistics.
    
    Uses proper variance combination formula to account for both
    within-chunk and between-chunk variance.
    """
    stats_dict = {
        "mean": {v: [] for v in variables},
        "std": {v: [] for v in variables},
        "log_mean": {v: [] for v in variables},
        "log_std": {v: [] for v in variables},
        "diff_mean": {v: [] for v in variables},
        "diff_std": {v: [] for v in variables},
    }
    
    # Collect all chunk statistics
    for chunk_stats in all_chunk_stats:
        if chunk_stats is None:
            continue
        
        for stat_type in stats_dict.keys():
            for var in variables:
                if var in chunk_stats[stat_type]:
                    stats_dict[stat_type][var].append(chunk_stats[stat_type][var])
    
    # Compute final statistics
    final_stats = {
        "mean": {},
        "std": {},
        "log_mean": {},
        "log_std": {},
        "diff_mean": {},
        "diff_std": {}
    }
    
    n = chunk_size
    for var in variables:
        if not stats_dict["mean"][var]:
            print(f"  Warning: No data for variable {var}")
            continue
        
        # Mean calculation (simple average of chunk means)
        final_stats["mean"][var] = np.mean(stats_dict["mean"][var])
        final_stats["log_mean"][var] = np.mean(stats_dict["log_mean"][var])
        final_stats["diff_mean"][var] = np.mean(stats_dict["diff_mean"][var])
        
        # Standard deviation calculation
        # Combine within-chunk and between-chunk variance
        # overall_var = mean_of_variances + variance_of_means
        
        # Standard data
        within_var = np.mean(np.square(stats_dict["std"][var]))
        between_var = np.var(stats_dict["mean"][var])
        final_stats["std"][var] = np.sqrt(within_var + between_var * (n-1)/n)
        
        # Log data
        within_var_log = np.mean(np.square(stats_dict["log_std"][var]))
        between_var_log = np.var(stats_dict["log_mean"][var])
        final_stats["log_std"][var] = np.sqrt(within_var_log + between_var_log * (n-1)/n)
        
        # Diff data
        within_var_diff = np.mean(np.square(stats_dict["diff_std"][var]))
        between_var_diff = np.var(stats_dict["diff_mean"][var])
        final_stats["diff_std"][var] = np.sqrt(within_var_diff + between_var_diff * (n-1)/n)
    
    # Convert to float for JSON serialization
    for stat_type, values in final_stats.items():
        final_stats[stat_type] = {var: float(val) for var, val in values.items()}
    
    return final_stats


def main():
    parser = argparse.ArgumentParser(
        description='Compute normalization parameters for ERA5-Land variables'
    )
    parser.add_argument(
        '--h5-dir',
        type=str,
        required=True,
        help='Directory containing IWB HDF5 files'
    )
    parser.add_argument(
        '--norm-params',
        type=str,
        required=True,
        help='Path to existing norm_params.json to update'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        default=2000,
        help='Start year for training period (default: 2000)'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        default=2017,
        help='End year for training period (default: 2017)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=100,
        help='Number of files per chunk (default: 100)'
    )
    parser.add_argument(
        '--num-workers',
        type=int,
        default=None,
        help='Number of parallel workers (default: auto)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("COMPUTE ERA5-LAND NORMALIZATION PARAMETERS")
    print("=" * 80)
    print(f"HDF5 directory: {args.h5_dir}")
    print(f"Norm params file: {args.norm_params}")
    print(f"Training period: {args.start_year}-{args.end_year}")
    print(f"Chunk size: {args.chunk_size}")
    
    # Get files for training period
    print(f"\nGetting HDF5 files for {args.start_year}-{args.end_year}...")
    train_files = get_h5_files_for_period(
        args.h5_dir, 
        args.start_year, 
        args.end_year
    )
    
    print(f"Found {len(train_files)} files in training period")
    
    if len(train_files) == 0:
        print("❌ No files found in training period!")
        return 1
    
    # Check if ERA5-Land variables exist in the files
    print("\nChecking for ERA5-Land variables...")
    with h5py.File(train_files[0], 'r') as f:
        available_era5_vars = [v for v in ERA5_LAND_VARS if v in f]
    
    if len(available_era5_vars) == 0:
        print(f"❌ No ERA5-Land variables found in {os.path.basename(train_files[0])}")
        print(f"   Expected: {ERA5_LAND_VARS}")
        print(f"   Run process_era5_land_netcdf.py first to integrate ERA5-Land data")
        return 1
    
    if len(available_era5_vars) < len(ERA5_LAND_VARS):
        print(f"⚠ Only found {len(available_era5_vars)} of {len(ERA5_LAND_VARS)} variables:")
        print(f"   Available: {available_era5_vars}")
        print(f"   Missing: {[v for v in ERA5_LAND_VARS if v not in available_era5_vars]}")
    else:
        print(f"✓ All {len(ERA5_LAND_VARS)} ERA5-Land variables found")
    
    # Create chunks
    num_full_chunks = len(train_files) // args.chunk_size
    full_chunk_files = train_files[:num_full_chunks * args.chunk_size]
    
    if len(full_chunk_files) < len(train_files):
        print(f"Note: Ignoring last {len(train_files) - len(full_chunk_files)} files for equal chunk sizes")
    
    chunks = []
    for i in range(0, len(full_chunk_files), args.chunk_size):
        chunks.append(full_chunk_files[i:i+args.chunk_size])
    
    print(f"Processing {len(chunks)} chunks...")
    
    # Determine number of workers
    if args.num_workers is None:
        num_workers = max(1, multiprocessing.cpu_count() // 2)
    else:
        num_workers = args.num_workers
    
    print(f"Using {num_workers} parallel workers")
    
    # Process chunks in parallel
    all_chunk_stats = []
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        future_to_chunk = {
            executor.submit(process_chunk, chunk, available_era5_vars): i 
            for i, chunk in enumerate(chunks)
        }
        
        # Collect results
        for future in tqdm(
            as_completed(future_to_chunk), 
            total=len(chunks), 
            desc="Processing chunks"
        ):
            chunk_idx = future_to_chunk[future]
            try:
                chunk_stats = future.result()
                all_chunk_stats.append(chunk_stats)
            except Exception as exc:
                print(f"\n  Warning: Chunk {chunk_idx} generated exception: {exc}")
    
    # Aggregate statistics
    print("\nAggregating statistics...")
    era5_stats = aggregate_statistics(all_chunk_stats, available_era5_vars, args.chunk_size)
    
    # Print computed statistics
    print("\n" + "=" * 80)
    print("COMPUTED STATISTICS")
    print("=" * 80)
    for var in available_era5_vars:
        print(f"\n{var}:")
        for stat_type in ['mean', 'std', 'diff_mean', 'diff_std']:
            if var in era5_stats[stat_type]:
                print(f"  {stat_type:12s}: {era5_stats[stat_type][var]:12.6e}")
    
    # Load existing norm_params.json
    print(f"\nLoading existing normalization parameters...")
    if os.path.exists(args.norm_params):
        with open(args.norm_params, 'r') as f:
            norm_params = json.load(f)
        print(f"✓ Loaded {len([k for k in norm_params.keys() if k not in ['lat', 'lon']])} existing variables")
    else:
        print(f"⚠ Normalization file not found, creating new one")
        norm_params = {"lat": [], "lon": []}
        
        # Get lat/lon from first HDF5 file if available
        try:
            with h5py.File(train_files[0], 'r') as f:
                if 'latitude' in f:
                    norm_params['lat'] = f['latitude'][:].tolist()
                if 'longitude' in f:
                    norm_params['lon'] = f['longitude'][:].tolist()
        except:
            pass
    
    # Update with ERA5-Land statistics
    print(f"\nUpdating normalization parameters...")
    for var in available_era5_vars:
        norm_params[var] = {
            "mean": era5_stats["mean"][var],
            "std": era5_stats["std"][var],
            "log_mean": era5_stats["log_mean"][var],
            "log_std": era5_stats["log_std"][var],
            "diff_mean": era5_stats["diff_mean"][var],
            "diff_std": era5_stats["diff_std"][var]
        }
        print(f"  ✓ Added/updated {var}")
    
    # Backup original file
    if os.path.exists(args.norm_params):
        backup_path = args.norm_params.replace('.json', '_backup.json')
        import shutil
        shutil.copy2(args.norm_params, backup_path)
        print(f"\nBackup saved to: {backup_path}")
    
    # Save updated normalization parameters
    with open(args.norm_params, 'w') as f:
        json.dump(norm_params, f, indent=4)
    
    print(f"\n✅ Updated normalization parameters saved to: {args.norm_params}")
    print(f"\nTotal variables in norm_params.json: {len([k for k in norm_params.keys() if k not in ['lat', 'lon']])}")
    
    print("\n" + "=" * 80)
    print("Next steps:")
    print("1. Validate integration: python scripts/validate_era5land_integration.py")
    print("2. Test data loading with new config")
    print("3. Train expanded model with 43 variables")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

