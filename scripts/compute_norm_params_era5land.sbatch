#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=compute_norm_era5land
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/compute_norm_era5land_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/compute_norm_era5land_%j.err
#SBATCH --time=4:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

echo "================================"
echo "Computing Normalization Parameters (Including ERA5-Land Variables)"
echo "Start time: $(date)"
echo "================================"

# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Navigate to IndiaWeatherBench directory
cd /burg-archive/home/mck2199/ML-Project

# First, backup the existing norm_params.json
if [ -f data/indibench_h5/norm_params.json ]; then
    cp data/indibench_h5/norm_params.json data/indibench_h5/norm_params_backup_$(date +%Y%m%d_%H%M%S).json
    echo "Backed up existing norm_params.json"
fi

# Run the normalization computation script
# This will compute statistics for ALL variables in the H5 files, including the new ERA5-Land variables
python scripts/compute_norm_params_modified.py \
    --root_dir /burg-archive/home/mck2199/ML-Project/data/indibench_h5 \
    --chunk_size 100 \
    --num_workers 16

# The script creates norm_params.json in the root_dir
echo ""
echo "================================"
echo "Normalization computation completed at $(date)"
echo "================================"

# Print summary of variables included
echo ""
echo "Variables included in normalization:"
python -c "
import json
with open('/burg-archive/home/mck2199/ML-Project/data/indibench_h5/norm_params.json', 'r') as f:
    params = json.load(f)
    print(f\"Total variables: {len(params['mean'])}\")
    for var in sorted(params['mean'].keys()):
        print(f\"  - {var}\")
"


