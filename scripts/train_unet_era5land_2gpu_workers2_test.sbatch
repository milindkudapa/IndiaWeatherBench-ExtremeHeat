#!/bin/bash
#SBATCH --account=glab
#SBATCH --job-name=train_era5land_workers2_test
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=8G
#SBATCH --time=02:00:00
#SBATCH --gres=gpu:2
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/train_unet_era5land_workers2_test_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/train_unet_era5land_workers2_test_%j.err

# Navigate to project root
cd /burg-archive/home/mck2199/ML-Project/IndiaWeatherBench || exit 1

# Activate environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Checkpoint directory - SEPARATE from main training
export TEST_CHECKPOINT_DIR="/burg-archive/home/mck2199/ML-Project/checkpoints_era5land_workers2_test"
mkdir -p $TEST_CHECKPOINT_DIR

# Disable HDF5 file locking system-wide
export HDF5_USE_FILE_LOCKING=FALSE

echo "========================================"
echo "ERA5-Land UNET Training - num_workers=2 TEST"
echo "========================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started: $(date)"
echo ""
echo "TEST Configuration:"
echo "  GPUs: 2 (DDP)"
echo "  Batch size: 16 per GPU (32 effective)"
echo "  Learning rate: 8e-4"
echo "  Data workers: 2 (TESTING - vs 0 in main job)"
echo "  Max epochs: 3 (limited for speed test)"
echo "  Checkpoints: $TEST_CHECKPOINT_DIR"
echo ""
echo "Comparing with Job 5066839 (num_workers=0)"
echo ""

# Run training with num_workers=2 and limited epochs
# This is a TEST - compare speed with main job
srun python train_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet_era5land.yaml \
    --trainer.devices=2 \
    --trainer.default_root_dir=$TEST_CHECKPOINT_DIR \
    --trainer.max_epochs=3 \
    --data.batch_size=16 \
    --model.lr=8e-4 \
    --data.num_workers=2
    
echo ""
echo "=========================================="
echo "Test completed at $(date)"
echo "=========================================="
echo ""
echo "Compare this speed with main job (5066839)"
echo "If faster and stable, we can use num_workers=2 for future runs"
echo ""

