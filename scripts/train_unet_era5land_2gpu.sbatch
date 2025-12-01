#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=train_unet_era5land
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/train_unet_era5land_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/train_unet_era5land_%j.err
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=8G
#SBATCH --gres=gpu:2
#SBATCH --constraint=a100
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

echo "=========================================="
echo "Training UNet with ERA5-Land Variables"
echo "=========================================="
echo "Start time: $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "GPUs: 2x A100"
echo ""

# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Disable HDF5 file locking for parallel dataloader access
export HDF5_USE_FILE_LOCKING=FALSE

# Navigate to project directory
cd /burg-archive/home/mck2199/ML-Project/IndiaWeatherBench

# Create separate checkpoint directory for ERA5-Land model
export ERA5_CHECKPOINT_DIR="/burg-archive/home/mck2199/ML-Project/checkpoints_era5land"
mkdir -p $ERA5_CHECKPOINT_DIR

echo "Configuration:"
echo "  Config: boundary_forcing_unet_era5land.yaml"
echo "  Variables: 45 (37 IWB + 6 ERA5-Land + 2 static)"
echo "  Input channels: 90 (2 steps × 45 vars)"
echo "  Batch size: 16 per GPU (32 effective)"
echo "  Learning rate: 8e-4 (scaled for larger batch)"
echo "  Data workers: 0 (single-process to avoid HDF5 issues)"
echo "  Checkpoints: $ERA5_CHECKPOINT_DIR"
echo ""

# Run the training with DDP (Distributed Data Parallel)
# Fixed: Removed 3 problematic files (1 missing ERA5-Land, 2 corrupted)
# Now all files are clean and DDP should work!
srun python train_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet_era5land.yaml \
    --trainer.devices=2 \
    --trainer.default_root_dir=$ERA5_CHECKPOINT_DIR \
    --data.batch_size=16 \
    --model.lr=8e-4 \
    --data.num_workers=0
    
echo ""
echo "=========================================="
echo "Training completed at $(date)"
echo "=========================================="
echo ""
echo "Checkpoints saved to: $ERA5_CHECKPOINT_DIR"
echo "WandB project: india-weatherbench-era5land"
echo ""

