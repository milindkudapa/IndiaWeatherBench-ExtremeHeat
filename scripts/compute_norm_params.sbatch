#!/bin/bash
#SBATCH --job-name=compute_norm
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/compute_norm_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/compute_norm_%j.err
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --partition=cpu
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

echo "================================"
echo "Computing normalization parameters"
echo "Start time: $(date)"
echo "================================"

# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Run the computation (using modified version of original script)
python /burg-archive/home/mck2199/ML-Project/scripts/compute_norm_params_modified.py \
    --root_dir /burg-archive/home/mck2199/ML-Project/data/indibench_h5 \
    --chunk_size 100 \
    --num_workers 8

echo ""
echo "================================"
echo "Computation complete!"
echo "End time: $(date)"
echo "================================"

