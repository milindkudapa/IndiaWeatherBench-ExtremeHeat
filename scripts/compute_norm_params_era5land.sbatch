#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=compute_norm_era5
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/compute_norm_era5_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/compute_norm_era5_%j.err
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

# ============================================================================
# Compute Normalization Parameters for ERA5-Land Variables
# ============================================================================
#
# This script computes statistics (mean, std, diff_mean, diff_std, etc.)
# for the 6 new ERA5-Land variables and updates norm_params.json
#
# Uses training period only: 2000-2017
#
# ============================================================================

set -e  # Exit on error

# Print start time
echo "========================================="
echo "ERA5-Land Normalization Computation"
echo "========================================="
echo "Start time: $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo ""

# Set project directory
PROJECT_DIR=/burg-archive/home/mck2199/ML-Project
cd $PROJECT_DIR

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check Python packages
echo ""
echo "Checking Python packages..."
python -c "import h5py, numpy, json; print('✓ All packages available')"

# Print configuration
echo ""
echo "Configuration:"
echo "  HDF5 directory: $PROJECT_DIR/data/indibench_h5"
echo "  Norm params file: $PROJECT_DIR/data/indibench_h5/norm_params.json"
echo "  Training period: 2000-2017"
echo "  Chunk size: 100 files"
echo "  Workers: 8"
echo ""

# Run computation script
echo "Starting computation..."
echo ""

python scripts/compute_norm_params_era5land.py \
    --h5-dir $PROJECT_DIR/data/indibench_h5 \
    --norm-params $PROJECT_DIR/data/indibench_h5/norm_params.json \
    --start-year 2000 \
    --end-year 2017 \
    --chunk-size 100 \
    --num-workers 8

# Print completion status
echo ""
echo "========================================="
echo "Computation Complete"
echo "========================================="
echo "End time: $(date)"
echo ""

# Verify norm_params.json
echo "Verifying updated norm_params.json..."
python << 'EOF'
import json
import os

norm_params_path = '/burg-archive/home/mck2199/ML-Project/data/indibench_h5/norm_params.json'
if os.path.exists(norm_params_path):
    with open(norm_params_path, 'r') as f:
        norm_params = json.load(f)
    
    era5_vars = ['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv']
    found_vars = [v for v in era5_vars if v in norm_params]
    
    print(f"  Total variables: {len([k for k in norm_params.keys() if k not in ['lat', 'lon']])}")
    print(f"  ERA5-Land variables: {len(found_vars)}/{len(era5_vars)}")
    
    if len(found_vars) == len(era5_vars):
        print(f"  ✓ All ERA5-Land variables have normalization parameters")
    else:
        missing = [v for v in era5_vars if v not in norm_params]
        print(f"  ⚠ Missing: {missing}")
else:
    print(f"  ⚠ File not found")
EOF

echo ""
echo "Job complete!"
