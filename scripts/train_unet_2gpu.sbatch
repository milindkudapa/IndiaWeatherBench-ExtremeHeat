#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=train_unet_2gpu
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/train_unet_2gpu_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/train_unet_2gpu_%j.err
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --gres=gpu:2
#SBATCH --constraint=a100
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

echo "================================"
echo "Training UNet with 2 GPUs"
echo "Start time: $(date)"
echo "================================"

# Load any required modules (adjust as needed for your HPC)
# module load cuda/12.1
# module load python/3.11

# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Navigate to project directory
cd /burg-archive/home/mck2199/ML-Project/IndiaWeatherBench

# Run the training with DDP (Distributed Data Parallel)
# Using srun to properly launch distributed training
srun python train_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet.yaml \
    --trainer.devices=2 \
    --data.batch_size=4

echo ""
echo "================================"
echo "Training completed at $(date)"
echo "================================"
