#!/bin/bash
#SBATCH --job-name=process_era5_land
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/process_era5land_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/process_era5land_%j.err
#SBATCH --time=08:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --account=glab
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

# ERA5-Land Data Processing and Integration
# This script processes all 240 months of ERA5-Land GeoTIFF data and integrates
# them into the existing IndiaWeatherBench HDF5 files.

set -e

echo "================================================================================================"
echo "ERA5-Land Data Integration - Starting at $(date)"
echo "================================================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Cores: $SLURM_CPUS_PER_TASK"
echo "Memory: ${SLURM_MEM_PER_NODE}MB"
echo "================================================================================================"
echo ""

# Navigate to project directory
cd /burg-archive/home/mck2199/ML-Project

# Activate virtual environment
source venv/bin/activate

# Verify Python environment
echo "Python: $(which python)"
echo "Python version: $(python --version)"
echo ""

# Run processing script
echo "Starting ERA5-Land GeoTIFF processing..."
echo "------------------------------------------------------------------------------------------------"

python IndiaWeatherBench/india_benchmark/data_processing/process_era5_land_geotiff.py \
    --era5land-dir /burg-archive/home/mck2199/ML-Project/data/era5_land_raw \
    --h5-output-dir /burg-archive/home/mck2199/ML-Project/data/indibench_h5 \
    --start-year 2000 \
    --end-year 2019

exit_code=$?

echo ""
echo "================================================================================================"
if [ $exit_code -eq 0 ]; then
    echo "Processing completed successfully at $(date)"
else
    echo "Processing failed with exit code $exit_code at $(date)"
fi
echo "================================================================================================"

exit $exit_code

