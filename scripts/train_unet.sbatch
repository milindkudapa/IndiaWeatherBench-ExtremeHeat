#!/bin/bash
#SBATCH --job-name=train_unet
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/train_unet_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/train_unet_%j.err
#SBATCH --time=18:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --constraint=a100
#SBATCH --account=glab
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

# Load any required modules (adjust as needed for your HPC)
# module load cuda/12.1
# module load python/3.11

# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Navigate to project directory
cd /burg-archive/home/mck2199/ML-Project/IndiaWeatherBench

# Run the training
# Using batch_size=8 for faster training on A100
python train_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet.yaml \
    --data.batch_size=8

echo "Job completed at $(date)"

