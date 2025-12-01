#!/usr/bin/env python3
"""
Validate ERA5-Land integration with IndiaWeatherBench HDF5 dataset.

This script checks:
1. All HDF5 files contain the new ERA5-Land variables
2. Shape consistency (256×256 for all variables)
3. No NaN or inf values in non-ocean regions
4. Reasonable value ranges for each variable
5. Temporal continuity
6. Normalization parameters are available
"""

import os
import sys
import argparse
import h5py
import numpy as np
import json
from datetime import datetime, timedelta
from tqdm import tqdm
import pandas as pd


# Expected ERA5-Land variables
ERA5_LAND_VARS = ['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv']

# Expected value ranges (rough physical limits)
VALUE_RANGES = {
    'swvl1': (0.0, 1.0),      # Volumetric soil moisture (m³/m³)
    'swvl2': (0.0, 1.0),      # Volumetric soil moisture (m³/m³)
    'slhf': (-1000.0, 1000.0),  # Surface latent heat flux (W/m²)
    'sshf': (-1000.0, 1000.0),  # Surface sensible heat flux (W/m²)
    'lai_hv': (0.0, 10.0),    # Leaf area index (m²/m²)
    'lai_lv': (0.0, 10.0)     # Leaf area index (m²/m²)
}


def check_single_file(h5_path, expected_shape=(256, 256)):
    """
    Check a single HDF5 file for ERA5-Land variables.
    
    Returns:
        dict: Results of checks
    """
    results = {
        'file': os.path.basename(h5_path),
        'exists': False,
        'vars_present': [],
        'vars_missing': [],
        'shape_ok': True,
        'range_ok': True,
        'has_nans': False,
        'has_infs': False,
        'errors': []
    }
    
    if not os.path.exists(h5_path):
        results['errors'].append('File not found')
        return results
    
    results['exists'] = True
    
    try:
        with h5py.File(h5_path, 'r') as f:
            available_vars = list(f.keys())
            
            # Check for ERA5-Land variables
            for var in ERA5_LAND_VARS:
                if var in available_vars:
                    results['vars_present'].append(var)
                    
                    # Check shape
                    data = f[var][:]
                    if data.shape != expected_shape:
                        results['shape_ok'] = False
                        results['errors'].append(
                            f'{var} has shape {data.shape}, expected {expected_shape}'
                        )
                    
                    # Check for NaN and Inf
                    if np.isnan(data).any():
                        results['has_nans'] = True
                    if np.isinf(data).any():
                        results['has_infs'] = True
                        results['errors'].append(f'{var} contains infinite values')
                    
                    # Check value range (only for non-NaN values)
                    valid_data = data[~np.isnan(data)]
                    if len(valid_data) > 0:
                        min_val, max_val = VALUE_RANGES[var]
                        data_min, data_max = valid_data.min(), valid_data.max()
                        
                        if data_min < min_val * 1.5 or data_max > max_val * 1.5:  # Allow 50% margin
                            results['range_ok'] = False
                            results['errors'].append(
                                f'{var} range [{data_min:.3f}, {data_max:.3f}] '
                                f'outside expected [{min_val}, {max_val}]'
                            )
                else:
                    results['vars_missing'].append(var)
    
    except Exception as e:
        results['errors'].append(f'Error reading file: {str(e)}')
    
    return results


def check_temporal_continuity(h5_dir, start_date, end_date):
    """
    Check that ERA5-Land data exists for all expected timesteps.
    """
    print("\nChecking temporal continuity...")
    
    current_date = start_date
    missing_files = []
    total_timesteps = 0
    
    while current_date <= end_date:
        for hour in [0, 6, 12, 18]:
            h5_filename = f"{current_date.strftime('%Y-%m-%d')}_{hour:02d}.h5"
            h5_path = os.path.join(h5_dir, h5_filename)
            
            if not os.path.exists(h5_path):
                missing_files.append(h5_filename)
            
            total_timesteps += 1
        
        current_date += timedelta(days=1)
    
    print(f"  Total expected timesteps: {total_timesteps}")
    print(f"  Missing files: {len(missing_files)}")
    
    if missing_files and len(missing_files) <= 10:
        print(f"  Missing file examples: {missing_files[:10]}")
    
    return len(missing_files) == 0


def check_normalization_params(norm_params_path):
    """
    Check if normalization parameters include ERA5-Land variables.
    """
    print("\nChecking normalization parameters...")
    
    if not os.path.exists(norm_params_path):
        print(f"  ⚠ Normalization file not found: {norm_params_path}")
        return False
    
    with open(norm_params_path, 'r') as f:
        norm_params = json.load(f)
    
    missing_vars = []
    for var in ERA5_LAND_VARS:
        if var not in norm_params:
            missing_vars.append(var)
        else:
            # Check that required statistics are present
            required_stats = ['mean', 'std', 'diff_mean', 'diff_std']
            for stat in required_stats:
                if stat not in norm_params[var]:
                    print(f"  ⚠ {var} missing statistic: {stat}")
    
    if missing_vars:
        print(f"  ⚠ Missing variables in norm_params.json: {missing_vars}")
        print(f"  → Run compute_norm_params.py to update normalization")
        return False
    else:
        print(f"  ✓ All ERA5-Land variables have normalization parameters")
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Validate ERA5-Land integration with IWB dataset'
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
        default=None,
        help='Path to norm_params.json (optional)'
    )
    parser.add_argument(
        '--sample-size',
        type=int,
        default=100,
        help='Number of files to sample for detailed checks (default: 100)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default='2000-01-01',
        help='Start date for temporal check (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        default='2019-12-31',
        help='End date for temporal check (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("ERA5-LAND INTEGRATION VALIDATION")
    print("=" * 80)
    print(f"HDF5 directory: {args.h5_dir}")
    print(f"Sample size: {args.sample_size} files")
    
    # Get list of all HDF5 files
    all_files = sorted([
        f for f in os.listdir(args.h5_dir)
        if f.endswith('.h5')
    ])
    
    print(f"\nTotal HDF5 files found: {len(all_files)}")
    
    if len(all_files) == 0:
        print("❌ No HDF5 files found!")
        return 1
    
    # Sample files for detailed checks
    sample_size = min(args.sample_size, len(all_files))
    if len(all_files) > sample_size:
        # Sample uniformly across the time period
        indices = np.linspace(0, len(all_files) - 1, sample_size, dtype=int)
        sample_files = [all_files[i] for i in indices]
    else:
        sample_files = all_files
    
    print(f"Checking {len(sample_files)} sample files...")
    
    # Check sample files
    all_results = []
    for fname in tqdm(sample_files, desc="Validating files"):
        h5_path = os.path.join(args.h5_dir, fname)
        result = check_single_file(h5_path)
        all_results.append(result)
    
    # Aggregate results
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    
    files_with_all_vars = sum(
        1 for r in all_results 
        if len(r['vars_present']) == len(ERA5_LAND_VARS)
    )
    files_with_no_vars = sum(
        1 for r in all_results 
        if len(r['vars_present']) == 0
    )
    files_with_errors = sum(1 for r in all_results if len(r['errors']) > 0)
    
    print(f"\n📊 Variable Presence:")
    print(f"  Files with all {len(ERA5_LAND_VARS)} ERA5-Land variables: {files_with_all_vars}/{len(sample_files)}")
    print(f"  Files with no ERA5-Land variables: {files_with_no_vars}/{len(sample_files)}")
    
    # Count presence of each variable
    var_counts = {var: 0 for var in ERA5_LAND_VARS}
    for result in all_results:
        for var in result['vars_present']:
            var_counts[var] += 1
    
    print(f"\n  Variable-wise presence:")
    for var, count in var_counts.items():
        percentage = (count / len(sample_files)) * 100
        print(f"    {var}: {count}/{len(sample_files)} ({percentage:.1f}%)")
    
    print(f"\n🔍 Data Quality:")
    shape_ok = sum(1 for r in all_results if r['shape_ok'])
    range_ok = sum(1 for r in all_results if r['range_ok'])
    has_nans = sum(1 for r in all_results if r['has_nans'])
    has_infs = sum(1 for r in all_results if r['has_infs'])
    
    print(f"  Shape correct (256×256): {shape_ok}/{len(sample_files)}")
    print(f"  Value ranges OK: {range_ok}/{len(sample_files)}")
    print(f"  Files with NaNs: {has_nans}/{len(sample_files)} (expected in ocean regions)")
    print(f"  Files with Infs: {has_infs}/{len(sample_files)} (should be 0)")
    
    if files_with_errors > 0:
        print(f"\n⚠ Errors found in {files_with_errors} files:")
        for result in all_results:
            if result['errors']:
                print(f"  {result['file']}:")
                for error in result['errors']:
                    print(f"    - {error}")
    
    # Check temporal continuity
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    temporal_ok = check_temporal_continuity(args.h5_dir, start_date, end_date)
    
    # Check normalization parameters
    norm_ok = True
    if args.norm_params:
        norm_ok = check_normalization_params(args.norm_params)
    
    # Final verdict
    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)
    
    all_checks_passed = (
        files_with_all_vars == len(sample_files) and
        files_with_errors == 0 and
        has_infs == 0 and
        temporal_ok and
        norm_ok
    )
    
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED!")
        print("\nERA5-Land integration is complete and validated.")
        print("Ready to train expanded model with 43 variables.")
        return 0
    else:
        print("⚠ SOME CHECKS FAILED")
        print("\nIssues to address:")
        if files_with_all_vars < len(sample_files):
            print("  - Not all files contain ERA5-Land variables")
            print("    → Run process_era5_land_netcdf.py to integrate data")
        if files_with_errors > 0:
            print("  - Some files have data quality issues")
            print("    → Review errors above and reprocess affected files")
        if has_infs > 0:
            print("  - Some files contain infinite values")
            print("    → Check preprocessing pipeline")
        if not temporal_ok:
            print("  - Missing timesteps detected")
            print("    → Verify IWB dataset completeness")
        if not norm_ok:
            print("  - Normalization parameters incomplete")
            print("    → Run compute_norm_params.py")
        return 1


if __name__ == '__main__':
    sys.exit(main())
