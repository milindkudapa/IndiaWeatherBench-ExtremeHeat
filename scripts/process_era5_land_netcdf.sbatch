#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=process_era5_netcdf
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/process_era5_netcdf_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/process_era5_netcdf_%j.err
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --partition=glab1
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

# ============================================================================
# Process ERA5-Land NetCDF Data from CDS and Integrate with IWB HDF5 Files
# ============================================================================
#
# This script:
# 1. Extracts NetCDF files from ZIP archives
# 2. Reads 6-hourly ERA5-Land data
# 3. Regrids from 0.1° to 0.12° resolution
# 4. Crops to IWB domain
# 5. Converts heat fluxes (J/m² → W/m²)
# 6. Adds 6 new variables to existing HDF5 files
#
# Input:  data/era5_land_cds/*.nc (ZIP archives)
# Output: data/indibench_h5/*.h5 (updated with 6 new variables)
#
# ============================================================================

set -e  # Exit on error

# Print start time
echo "========================================="
echo "ERA5-Land CDS NetCDF Processing Started"
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
python -c "import xarray, h5py, scipy, numpy; print('✓ All packages available')"

# Print configuration
echo ""
echo "Configuration:"
echo "  ERA5-Land CDS directory: $PROJECT_DIR/data/era5_land_cds"
echo "  HDF5 output directory: $PROJECT_DIR/data/indibench_h5"
echo "  Start year: 2000"
echo "  End year: 2019"
echo "  Variables: swvl1, swvl2, slhf, sshf, lai_hv, lai_lv"
echo ""

# Count input files
NUM_FILES=$(ls data/era5_land_cds/era5_land_hourly_*.nc 2>/dev/null | wc -l)
echo "Found $NUM_FILES ERA5-Land CDS files to process"
echo ""

# Run processing script
echo "Starting processing..."
echo ""

python IndiaWeatherBench/india_benchmark/data_processing/process_era5_land_netcdf.py \
    --era5land-dir $PROJECT_DIR/data/era5_land_cds \
    --h5-output-dir $PROJECT_DIR/data/indibench_h5 \
    --start-year 2000 \
    --end-year 2019

# Print completion status
echo ""
echo "========================================="
echo "Processing Complete"
echo "========================================="
echo "End time: $(date)"
echo ""

# Verify a sample file
echo "Verifying sample updated HDF5 file..."
python << 'EOF'
import h5py
import os

# Check a sample file
sample_file = '/burg-archive/home/mck2199/ML-Project/data/indibench_h5/2000-01-01_00.h5'
if os.path.exists(sample_file):
    with h5py.File(sample_file, 'r') as f:
        variables = list(f.keys())
        print(f"  Total variables: {len(variables)}")
        
        era5_vars = [v for v in ['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv'] if v in variables]
        if era5_vars:
            print(f"  ERA5-Land variables found: {era5_vars}")
            print(f"  ✓ Integration successful!")
        else:
            print(f"  ⚠ ERA5-Land variables not found")
else:
    print(f"  Sample file not found")
EOF

echo ""
echo "Next steps:"
echo "1. Compute normalization parameters for new variables"
echo "2. Create new training config with 43 variables"
echo "3. Validate integration"
echo "4. Train expanded model"
echo ""
echo "Job complete!"

