#!/usr/bin/env python3
"""
Validate ERA5-Land integration with IndiaWeatherBench dataset.

This script performs several checks to ensure the ERA5-Land variables
have been correctly integrated into the HDF5 files and can be loaded
by the dataloader.

Checks performed:
1. Verify all HDF5 files contain ERA5-Land variables
2. Check shape consistency (256x256 for all variables)
3. Check for NaN or inf values
4. Verify reasonable value ranges
5. Test dataloader with new configuration
6. Check normalization parameters
"""

import os
import sys
import h5py
import numpy as np
import json
import argparse
from glob import glob
from tqdm import tqdm

# Add IndiaWeatherBench to path
sys.path.insert(0, '/burg-archive/home/mck2199/ML-Project/IndiaWeatherBench')

from india_benchmark.datasets.datamodule import IndiaDataModule


# Expected value ranges for ERA5-Land variables (rough estimates)
EXPECTED_RANGES = {
    'swvl1': (0.0, 0.6),  # m³/m³ volumetric soil moisture
    'swvl2': (0.0, 0.6),  # m³/m³ volumetric soil moisture
    'slhf': (-500, 500),  # W/m² surface latent heat flux
    'sshf': (-300, 300),  # W/m² surface sensible heat flux
    'lai_hv': (0.0, 10.0),  # m²/m² leaf area index
    'lai_lv': (0.0, 10.0),  # m²/m² leaf area index
}


def check_h5_file(h5_path, era5_variables):
    """
    Check a single HDF5 file for ERA5-Land variables.
    
    Returns:
        dict: Status of checks
    """
    result = {
        'path': h5_path,
        'has_all_vars': True,
        'missing_vars': [],
        'shape_issues': [],
        'nan_inf_issues': [],
        'range_issues': []
    }
    
    try:
        with h5py.File(h5_path, 'r') as f:
            available_vars = list(f.keys())
            
            # Check for presence of ERA5-Land variables
            for var in era5_variables:
                if var not in available_vars:
                    result['has_all_vars'] = False
                    result['missing_vars'].append(var)
                else:
                    # Check shape
                    data = f[var][:]
                    if data.shape != (256, 256):
                        result['shape_issues'].append(
                            f"{var}: shape is {data.shape}, expected (256, 256)"
                        )
                    
                    # Check for NaN/inf
                    if np.any(np.isnan(data)) or np.any(np.isinf(data)):
                        result['nan_inf_issues'].append(
                            f"{var}: contains NaN or inf values"
                        )
                    
                    # Check value range
                    if var in EXPECTED_RANGES:
                        vmin, vmax = EXPECTED_RANGES[var]
                        data_min, data_max = np.nanmin(data), np.nanmax(data)
                        # Allow some tolerance
                        if data_min < vmin * 2 or data_max > vmax * 2:
                            result['range_issues'].append(
                                f"{var}: range [{data_min:.3f}, {data_max:.3f}] "
                                f"outside expected [{vmin}, {vmax}]"
                            )
    
    except Exception as e:
        result['error'] = str(e)
    
    return result


def check_all_h5_files(data_dir, era5_variables, sample_size=100):
    """
    Check a sample of HDF5 files for ERA5-Land variables.
    """
    print("=" * 80)
    print("Checking HDF5 files for ERA5-Land variables...")
    print("=" * 80)
    
    all_issues = []
    
    for split in ['train', 'val', 'test']:
        split_dir = os.path.join(data_dir, split)
        if not os.path.exists(split_dir):
            print(f"\nWarning: {split} directory not found: {split_dir}")
            continue
        
        h5_files = sorted(glob(os.path.join(split_dir, "*.h5")))
        
        # Sample files
        if len(h5_files) > sample_size:
            import random
            random.seed(42)
            h5_files = random.sample(h5_files, sample_size)
        
        print(f"\n{split.upper()} split: Checking {len(h5_files)} files...")
        
        has_era5_count = 0
        
        for h5_file in tqdm(h5_files, desc=f"Checking {split}"):
            result = check_h5_file(h5_file, era5_variables)
            
            if result['has_all_vars']:
                has_era5_count += 1
            
            # Collect issues
            if not result['has_all_vars'] or result['shape_issues'] or \
               result['nan_inf_issues'] or result['range_issues']:
                all_issues.append(result)
        
        print(f"  Files with all ERA5-Land variables: {has_era5_count}/{len(h5_files)}")
    
    return all_issues


def check_normalization_params(norm_params_path, era5_variables):
    """
    Check that normalization parameters include ERA5-Land variables.
    """
    print("\n" + "=" * 80)
    print("Checking normalization parameters...")
    print("=" * 80)
    
    if not os.path.exists(norm_params_path):
        print(f"ERROR: Normalization parameters not found: {norm_params_path}")
        return False
    
    with open(norm_params_path, 'r') as f:
        norm_params = json.load(f)
    
    all_vars_present = True
    for var in era5_variables:
        if var not in norm_params['mean']:
            print(f"  ERROR: {var} not in normalization parameters")
            all_vars_present = False
        else:
            print(f"  ✓ {var}:")
            print(f"    mean: {norm_params['mean'][var]:.6f}")
            print(f"    std:  {norm_params['std'][var]:.6f}")
    
    return all_vars_present


def test_dataloader(config_path, era5_variables):
    """
    Test loading data with the new configuration.
    """
    print("\n" + "=" * 80)
    print("Testing dataloader with ERA5-Land variables...")
    print("=" * 80)
    
    try:
        import yaml
        import torch
        
        # Load config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Create datamodule
        datamodule = IndiaDataModule(
            **config['data']
        )
        
        datamodule.setup()
        
        # Get a batch from training data
        train_loader = datamodule.train_dataloader()
        X, Y = next(iter(train_loader))
        
        print(f"\n✓ Successfully loaded a batch!")
        print(f"  Input shape:  {X.shape}")  # Should be (B, T, C, H, W) where C=43
        print(f"  Output shape: {Y.shape}")
        
        expected_channels = len(config['data']['variables'])
        actual_channels = X.shape[2]
        
        if actual_channels == expected_channels:
            print(f"  ✓ Number of channels matches: {actual_channels}")
        else:
            print(f"  ERROR: Expected {expected_channels} channels, got {actual_channels}")
            return False
        
        # Check for NaN in batch
        if torch.any(torch.isnan(X)) or torch.any(torch.isnan(Y)):
            print("  ERROR: Batch contains NaN values!")
            return False
        else:
            print("  ✓ No NaN values in batch")
        
        print("\n✓ Dataloader test passed!")
        return True
        
    except Exception as e:
        print(f"\nERROR testing dataloader: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Validate ERA5-Land integration'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='/burg-archive/home/mck2199/ML-Project/data/indibench_h5',
        help='Path to HDF5 data directory'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='/burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet_era5land.yaml',
        help='Path to new config file'
    )
    parser.add_argument(
        '--sample-size',
        type=int,
        default=100,
        help='Number of files to check per split'
    )
    parser.add_argument(
        '--skip-dataloader-test',
        action='store_true',
        help='Skip dataloader test (useful if data not fully processed yet)'
    )
    
    args = parser.parse_args()
    
    era5_variables = ['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv']
    
    print("\n" + "=" * 80)
    print("ERA5-Land Integration Validation")
    print("=" * 80)
    print(f"Data directory: {args.data_dir}")
    print(f"Config file: {args.config}")
    print(f"ERA5-Land variables: {', '.join(era5_variables)}")
    print("=" * 80)
    
    # Check 1: HDF5 files
    issues = check_all_h5_files(args.data_dir, era5_variables, args.sample_size)
    
    if issues:
        print("\n" + "=" * 80)
        print("ISSUES FOUND:")
        print("=" * 80)
        for issue in issues[:10]:  # Show first 10
            print(f"\nFile: {os.path.basename(issue['path'])}")
            if issue.get('missing_vars'):
                print(f"  Missing variables: {', '.join(issue['missing_vars'])}")
            if issue.get('shape_issues'):
                for msg in issue['shape_issues']:
                    print(f"  Shape issue: {msg}")
            if issue.get('nan_inf_issues'):
                for msg in issue['nan_inf_issues']:
                    print(f"  NaN/Inf issue: {msg}")
            if issue.get('range_issues'):
                for msg in issue['range_issues']:
                    print(f"  Range issue: {msg}")
        
        if len(issues) > 10:
            print(f"\n... and {len(issues) - 10} more files with issues")
    else:
        print("\n✓ All checked files passed basic validation!")
    
    # Check 2: Normalization parameters
    norm_params_path = os.path.join(args.data_dir, 'norm_params.json')
    norm_ok = check_normalization_params(norm_params_path, era5_variables)
    
    # Check 3: Dataloader (optional)
    if not args.skip_dataloader_test:
        dataloader_ok = test_dataloader(args.config, era5_variables)
    else:
        print("\nSkipping dataloader test (--skip-dataloader-test flag set)")
        dataloader_ok = None
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"HDF5 files check: {'✓ PASSED' if not issues else f'⚠ {len(issues)} issues found'}")
    print(f"Normalization check: {'✓ PASSED' if norm_ok else '✗ FAILED'}")
    if dataloader_ok is not None:
        print(f"Dataloader check: {'✓ PASSED' if dataloader_ok else '✗ FAILED'}")
    print("=" * 80)
    
    # Exit code
    if issues or not norm_ok or (dataloader_ok is False):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()


