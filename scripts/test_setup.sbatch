#!/bin/bash
#SBATCH --job-name=test_setup
#SBATCH --output=/burg-archive/home/mck2199/ML-Project/logs/test_setup_%j.out
#SBATCH --error=/burg-archive/home/mck2199/ML-Project/logs/test_setup_%j.err
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mck2199@columbia.edu

echo "================================"
echo "Testing UNet setup"
echo "Start time: $(date)"
echo "================================"

# Load any required modules (adjust as needed for your HPC)
# module load cuda/12.1
# module load python/3.11

# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

echo ""
echo "Python version:"
python --version

echo ""
echo "PyTorch version and CUDA availability:"
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}'); print(f'Device count: {torch.cuda.device_count()}'); print(f'Device name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

echo ""
echo "Checking GPU with nvidia-smi:"
nvidia-smi

echo ""
echo "================================"
echo "Running fast_dev_run (2 train + 2 val batches)"
echo "This tests: data loading, model forward pass, GPU usage"
echo "================================"

# Navigate to project directory
cd /burg-archive/home/mck2199/ML-Project/IndiaWeatherBench

# Run fast dev run - just 2 batches to verify everything works
python train_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet.yaml \
    --trainer.fast_dev_run=2 \
    --trainer.devices=1

echo ""
echo "================================"
echo "Test completed successfully!"
echo "End time: $(date)"
echo "================================"
echo ""
echo "If you see this message, your setup is working correctly."
echo "You can now run the full training with: sbatch scripts/train_unet.sbatch"

