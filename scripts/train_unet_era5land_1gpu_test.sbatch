#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=train_era5land_1gpu_test
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=8G
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:1
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/train_unet_era5land_1gpu_test_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/train_unet_era5land_1gpu_test_%j.err

# Navigate to project root
cd /burg-archive/home/mck2199/ML-Project/IndiaWeatherBench || exit 1

# Activate environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Checkpoint directory
export ERA5_CHECKPOINT_DIR="/burg-archive/home/mck2199/ML-Project/checkpoints_era5land"

# Disable HDF5 file locking system-wide
export HDF5_USE_FILE_LOCKING=FALSE

echo "================================"
echo "ERA5-Land UNET Training TEST (1 GPU)"
echo "================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "GPUs: 1"
echo "Time: $(date)"
echo ""

# Test with 1 GPU only, limit to 2 epochs
python train_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet_era5land.yaml \
    --trainer.devices=1 \
    --trainer.default_root_dir=$ERA5_CHECKPOINT_DIR \
    --trainer.max_epochs=2 \
    --trainer.limit_train_batches=10 \
    --trainer.limit_val_batches=5 \
    --data.batch_size=8 \
    --model.lr=4e-4 \
    --data.num_workers=0

echo "Test training completed"

