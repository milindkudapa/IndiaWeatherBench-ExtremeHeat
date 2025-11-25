#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=process_era5land
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/process_era5land_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/process_era5land_%j.err
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

echo "================================"
echo "Processing ERA5-Land Data"
echo "Start time: $(date)"
echo "================================"

# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Navigate to IndiaWeatherBench directory
cd /burg-archive/home/mck2199/ML-Project/IndiaWeatherBench

# Run the preprocessing script
python india_benchmark/data_processing/process_era5_land.py \
    --era5land-dir /burg-archive/home/mck2199/ML-Project/data/era5_land_raw \
    --h5-output-dir /burg-archive/home/mck2199/ML-Project/data/indibench_h5 \
    --start-year 2000 \
    --end-year 2019 \
    --num-workers 4

echo ""
echo "================================"
echo "Processing completed at $(date)"
echo "================================"


