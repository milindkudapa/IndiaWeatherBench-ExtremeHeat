#!/usr/bin/env python3
"""
Check ERA5-Land data quality in HDF5 files
- Verify all 6 ERA5-Land variables exist
- Check for NaN, Inf, or extreme values
- Sample multiple files from train/val/test splits
"""
import h5py
import numpy as np
import os
from pathlib import Path
import random

def check_file(filepath, era5_vars):
    """Check a single HDF5 file for data quality issues"""
    issues = []
    stats = {}
    
    try:
        with h5py.File(filepath, 'r', locking=False) as f:
            for var in era5_vars:
                if var not in f:
                    issues.append(f"❌ {var}: NOT FOUND")
                    continue
                
                data = f[var][()]
                
                # Check for NaN
                nan_count = np.isnan(data).sum()
                if nan_count > 0:
                    issues.append(f"❌ {var}: {nan_count} NaN values ({100*nan_count/data.size:.2f}%)")
                
                # Check for Inf
                inf_count = np.isinf(data).sum()
                if inf_count > 0:
                    issues.append(f"❌ {var}: {inf_count} Inf values ({100*inf_count/data.size:.2f}%)")
                
                # Store statistics
                if nan_count == 0 and inf_count == 0:
                    stats[var] = {
                        'min': float(np.min(data)),
                        'max': float(np.max(data)),
                        'mean': float(np.mean(data)),
                        'std': float(np.std(data))
                    }
                    
                    # Check for extreme values (sanity check)
                    if abs(stats[var]['mean']) > 1e10:
                        issues.append(f"⚠️  {var}: Extreme mean value {stats[var]['mean']}")
                    if stats[var]['std'] > 1e10:
                        issues.append(f"⚠️  {var}: Extreme std value {stats[var]['std']}")
                        
    except Exception as e:
        issues.append(f"❌ ERROR reading file: {e}")
    
    return issues, stats

def main():
    print("=" * 80)
    print("ERA5-LAND DATA QUALITY CHECK")
    print("=" * 80)
    
    h5_dir = Path('/burg-archive/home/mck2199/ML-Project/data/indibench_h5')
    era5_vars = ['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv']
    
    # Sample files from each split
    all_files = []
    for split in ['train', 'val', 'test']:
        split_dir = h5_dir / split
        if split_dir.exists():
            files = sorted(list(split_dir.glob('*.h5')))
            # Sample 5 random files from each split
            sample_size = min(5, len(files))
            sampled = random.sample(files, sample_size)
            all_files.extend([(split, f) for f in sampled])
    
    print(f"\nChecking {len(all_files)} sampled files...")
    print(f"Variables to check: {', '.join(era5_vars)}\n")
    
    all_issues = []
    file_stats = {}
    
    for split, filepath in all_files:
        filename = filepath.name
        issues, stats = check_file(filepath, era5_vars)
        
        if issues:
            print(f"\n{split}/{filename}:")
            for issue in issues:
                print(f"  {issue}")
            all_issues.extend(issues)
        else:
            print(f"✅ {split}/{filename}: All ERA5-Land variables OK")
            file_stats[filename] = stats
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if all_issues:
        print(f"\n⚠️  FOUND {len(all_issues)} ISSUES:")
        for issue in set(all_issues):
            print(f"  {issue}")
    else:
        print("\n✅ ALL SAMPLED FILES ARE CLEAN!")
        print("\nSample statistics from one file:")
        if file_stats:
            first_file = list(file_stats.keys())[0]
            for var, stats in file_stats[first_file].items():
                print(f"  {var}:")
                print(f"    min={stats['min']:.4f}, max={stats['max']:.4f}")
                print(f"    mean={stats['mean']:.4f}, std={stats['std']:.4f}")
    
    print("\n" + "=" * 80)
    
    return len(all_issues) == 0

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)

