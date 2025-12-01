#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=train_era5land
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem-per-cpu=8G
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:1
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/train_unet_era5land_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/train_unet_era5land_%j.err

# Navigate to project root
cd /burg-archive/home/mck2199/ML-Project/IndiaWeatherBench || exit 1

# Activate environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Checkpoint directory
export ERA5_CHECKPOINT_DIR="/burg-archive/home/mck2199/ML-Project/checkpoints_era5land"

# Disable HDF5 file locking system-wide (just in case)
export HDF5_USE_FILE_LOCKING=FALSE

echo "========================================"
echo "ERA5-Land UNET Training (1 GPU - STABLE)"
echo "========================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started: $(date)"
echo ""
echo "Configuration:"
echo "  Config: boundary_forcing_unet_era5land.yaml"
echo "  Variables: 45 (37 IWB + 6 ERA5-Land + 2 static)"
echo "  Input channels: 90 (2 steps × 45 vars)"
echo "  GPUs: 1"
echo "  Batch size: 16"
echo "  Learning rate: 4e-4"
echo "  Data workers: 0 (single-process loading)"
echo "  Checkpoints: $ERA5_CHECKPOINT_DIR"
echo ""

# Run training with 1 GPU
# Using large batch size since we have plenty of GPU memory
# Conservative learning rate
python train_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet_era5land.yaml \
    --trainer.devices=1 \
    --trainer.default_root_dir=$ERA5_CHECKPOINT_DIR \
    --data.batch_size=16 \
    --model.lr=4e-4 \
    --data.num_workers=0

echo "Training completed at $(date)"

