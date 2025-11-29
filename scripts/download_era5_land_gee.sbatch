#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=download_era5_gee
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/download_era5_gee_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/download_era5_gee_%j.err
#SBATCH --time=48:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

echo "================================"
echo "Downloading ERA5-Land via Google Earth Engine"
echo "Start time: $(date)"
echo "================================"

# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Check if Earth Engine is authenticated
if ! python -c "import ee; ee.Initialize()" 2>/dev/null; then
    echo "ERROR: Earth Engine not authenticated!"
    echo "Please run: earthengine authenticate"
    exit 1
fi

echo "Earth Engine authenticated successfully"
echo ""

# Create output directory
mkdir -p /burg-archive/home/mck2199/ML-Project/data/era5_land_raw

# Run the download script using geemap
python /burg-archive/home/mck2199/ML-Project/scripts/download_era5_land_geemap.py \
    --output-dir /burg-archive/home/mck2199/ML-Project/data/era5_land_raw \
    --start-year 2000 \
    --end-year 2019 \
    --variables swvl1 swvl2 slhf sshf lai_hv lai_lv

echo ""
echo "================================"
echo "Download completed at $(date)"
echo "================================"

