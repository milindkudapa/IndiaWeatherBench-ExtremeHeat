#!/bin/bash
#SBATCH --job-name=test_persistence
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/persistence_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/persistence_%j.err
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

# Load any required modules (adjust as needed for your HPC)
# module load cuda/12.1
# module load python/3.11

# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Navigate to project directory
cd /burg-archive/home/mck2199/ML-Project/IndiaWeatherBench

# Run the test
python test_persistence.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/persistence.yaml

echo "Job completed at $(date)"

