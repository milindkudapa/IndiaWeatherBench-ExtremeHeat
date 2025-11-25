#!/bin/bash

# Script to test UNet in an interactive session
# Run this AFTER getting an interactive GPU node with salloc or srun

echo "================================"
echo "Interactive UNet Test"
echo "================================"
echo ""
echo "Make sure you're on a GPU node!"
echo "If not, request one first with:"
echo "  salloc --partition=gpu --gres=gpu:1 --mem=32G --cpus-per-task=4 --time=01:00:00"
echo ""

# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

echo "Python version:"
python --version

echo ""
echo "PyTorch and CUDA info:"
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

echo ""
echo "GPU status:"
nvidia-smi

echo ""
echo "================================"
echo "Running fast_dev_run test..."
echo "================================"

cd /burg-archive/home/mck2199/ML-Project/IndiaWeatherBench

python train_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet.yaml \
    --trainer.fast_dev_run=2 \
    --trainer.devices=1

echo ""
echo "================================"
echo "Test complete!"
echo "================================"

