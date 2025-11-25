#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=download_era5land
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/download_era5land_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/download_era5land_%j.err
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

echo "================================"
echo "Downloading ERA5-Land Data"
echo "Start time: $(date)"
echo "================================"

# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Check if CDS API credentials are configured
if [ ! -f ~/.cdsapirc ]; then
    echo "ERROR: CDS API credentials not found!"
    echo "Please create ~/.cdsapirc with your Copernicus CDS credentials."
    echo "See: https://cds.climate.copernicus.eu/how-to-api"
    exit 1
fi

# Create output directory
mkdir -p /burg-archive/home/mck2199/ML-Project/data/era5_land_raw

# Run the download script
python /burg-archive/home/mck2199/ML-Project/scripts/download_era5_land.py \
    --output-dir /burg-archive/home/mck2199/ML-Project/data/era5_land_raw \
    --start-year 2000 \
    --end-year 2019 \
    --variables swvl1 swvl2 slhf sshf lai_hv lai_lv

echo ""
echo "================================"
echo "Download completed at $(date)"
echo "================================"


