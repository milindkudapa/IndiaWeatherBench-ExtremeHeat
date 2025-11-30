#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=era5_hourly_gee
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/download_era5_hourly_gee_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/download_era5_hourly_gee_%j.err
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

# ERA5-Land Hourly Data Download via Google Earth Engine
# Queues batch export tasks to Google Drive
# Downloads 6-hourly timesteps (00, 06, 12, 18 UTC) day-by-day
# Files exported to YOUR Google Drive (must download manually)

set -e

echo "================================================================================================"
echo "ERA5-Land Hourly Download (Google Earth Engine) - Starting at $(date)"
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

# Check if authenticated
echo "Checking Google Earth Engine authentication..."
python -c "import ee; ee.Initialize(); print('✓ GEE authenticated')" || {
    echo "✗ Not authenticated!"
    echo ""
    echo "Please run authentication first:"
    echo "  python scripts/authenticate_gee.py"
    echo ""
    exit 1
}

echo ""
echo "Starting GEE batch export queue..."
echo "Export destination: Your Google Drive > era5_land_gee/ folder"
echo "Local tracking directory: data/era5_land_gee/"
echo "Time period: 2000-2019"
echo "Timesteps per day: 4 (00, 06, 12, 18 UTC)"
echo "Total files: ~7,305 (one per day)"
echo "------------------------------------------------------------------------------------------------"

python scripts/download_era5_land_hourly_gee.py \
    --output-dir /burg-archive/home/mck2199/ML-Project/data/era5_land_gee \
    --start-year 2000 \
    --end-year 2019 \
    --max-concurrent 100

exit_code=$?

echo ""
echo "================================================================================================"
if [ $exit_code -eq 0 ]; then
    echo "✓ Export tasks queued successfully at $(date)"
    echo ""
    echo "NEXT STEPS:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "1. Monitor tasks at: https://code.earthengine.google.com/tasks"
    echo ""
    echo "2. After tasks complete, download from Google Drive:"
    echo "   - Go to: https://drive.google.com"
    echo "   - Navigate to folder: era5_land_gee"
    echo "   - Download all files"
    echo ""
    echo "3. Transfer to HPC:"
    echo "   scp era5_land_*.tif mck2199@bader:/burg-archive/home/mck2199/ML-Project/data/era5_land_gee/"
    echo ""
    echo "4. Or use rclone to sync directly from Drive to HPC"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "✗ Export queue failed with exit code $exit_code at $(date)"
fi
echo "================================================================================================"

exit $exit_code

