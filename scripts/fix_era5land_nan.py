#!/usr/bin/env python3
"""
Fix NaN values in ERA5-Land variables
Strategy: Fill NaN with 0 (appropriate for ocean areas)
"""
import h5py
import numpy as np
from pathlib import Path
from tqdm import tqdm
import argparse

def fix_file(filepath, era5_vars, dry_run=False):
    """Fix NaN values in a single HDF5 file"""
    fixed_count = 0
    
    try:
        mode = 'r' if dry_run else 'a'
        with h5py.File(filepath, mode, locking=False) as f:
            for var in era5_vars:
                if var not in f:
                    continue
                
                data = f[var][()]
                nan_mask = np.isnan(data)
                nan_count = nan_mask.sum()
                
                if nan_count > 0:
                    if not dry_run:
                        # Fill NaN with 0 (ocean areas have no soil moisture, heat flux, etc.)
                        data[nan_mask] = 0.0
                        # Update dataset
                        f[var][...] = data
                    fixed_count += nan_count
                    
    except Exception as e:
        print(f"ERROR processing {filepath}: {e}")
        return 0
    
    return fixed_count

def main():
    parser = argparse.ArgumentParser(description='Fix NaN values in ERA5-Land HDF5 files')
    parser.add_argument('--dry-run', action='store_true', help='Count NaNs without fixing')
    parser.add_argument('--split', type=str, default=None, help='Process only this split (train/val/test)')
    args = parser.parse_args()
    
    print("=" * 80)
    print("FIX ERA5-LAND NaN VALUES" if not args.dry_run else "COUNT ERA5-LAND NaN VALUES (DRY RUN)")
    print("=" * 80)
    
    h5_dir = Path('/burg-archive/home/mck2199/ML-Project/data/indibench_h5')
    era5_vars = ['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv']
    
    # Get all files
    all_files = []
    splits = [args.split] if args.split else ['train', 'val', 'test']
    
    for split in splits:
        split_dir = h5_dir / split
        if split_dir.exists():
            files = sorted(list(split_dir.glob('*.h5')))
            all_files.extend(files)
    
    print(f"\nProcessing {len(all_files)} files...")
    print(f"Strategy: Fill NaN values with 0.0 (appropriate for ocean areas)")
    print(f"Variables: {', '.join(era5_vars)}\n")
    
    total_fixed = 0
    
    for filepath in tqdm(all_files, desc="Processing"):
        fixed = fix_file(filepath, era5_vars, dry_run=args.dry_run)
        total_fixed += fixed
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files processed: {len(all_files)}")
    print(f"Total NaN values {'found' if args.dry_run else 'fixed'}: {total_fixed:,}")
    print(f"Per file average: {total_fixed/len(all_files):.0f} NaN values")
    
    if args.dry_run:
        print(f"\n⚠️  DRY RUN - No changes made")
        print(f"   Run without --dry-run to actually fix the files")
    else:
        print(f"\n✅ All NaN values filled with 0.0!")
        print(f"   Training should now work without NaN loss")
    
    print("=" * 80)

if __name__ == '__main__':
    main()

