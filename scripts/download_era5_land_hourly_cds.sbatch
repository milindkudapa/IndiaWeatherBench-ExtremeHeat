#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=era5_hourly_cds
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/download_era5_hourly_cds_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/download_era5_hourly_cds_%j.err
#SBATCH --time=48:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

# ERA5-Land Hourly Data Download via Copernicus CDS API
# Downloads 6-hourly timesteps (00, 06, 12, 18 UTC) month-by-month
# Files saved directly to HPC in NetCDF format (compressed)

set -e

echo "================================================================================================"
echo "ERA5-Land Hourly Download (CDS API) - Starting at $(date)"
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

# Run download script
echo "Starting CDS API download..."
echo "Output directory: data/era5_land_cds/"
echo "Time period: 2000-2019"
echo "Timesteps: 00, 06, 12, 18 UTC (6-hourly)"
echo "------------------------------------------------------------------------------------------------"

python scripts/download_era5_land_hourly.py \
    --output-dir /burg-archive/home/mck2199/ML-Project/data/era5_land_cds \
    --start-year 2000 \
    --end-year 2019

exit_code=$?

echo ""
echo "================================================================================================"
if [ $exit_code -eq 0 ]; then
    echo "✓ Download completed successfully at $(date)"
    echo ""
    echo "IMPORTANT: Files are compressed (zip format)"
    echo "You need to extract them before processing:"
    echo "  cd data/era5_land_cds"
    echo "  for f in era5_land_hourly_*.nc; do"
    echo "    unzip -o \$f && mv data_0.nc \${f%.nc}_extracted.nc"
    echo "  done"
else
    echo "✗ Download failed with exit code $exit_code at $(date)"
    echo ""
    echo "Check logs for failed months and retry individually if needed."
fi
echo "================================================================================================"

exit $exit_code

