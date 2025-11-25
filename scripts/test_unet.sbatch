#!/bin/bash
#SBATCH --job-name=test_unet
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/test_unet_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/test_unet_%j.err
#SBATCH --time=04:00:00
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

# Set checkpoint path (modify this to your actual checkpoint)
CKPT_PATH="/burg-archive/home/mck2199/ML-Project/checkpoints/boundary_forcing_unet/last.ckpt"

# Run the test
python test_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet.yaml \
    --ckpt_path $CKPT_PATH

echo "Job completed at $(date)"

