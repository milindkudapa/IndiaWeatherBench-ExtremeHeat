# IndiaWeatherBench UNet Implementation

This directory contains the setup for training a UNet model for regional weather forecasting over India, based on the IndiaWeatherBench paper.

## Setup Complete ✓

- ✓ IndiaWeatherBench repository cloned
- ✓ Python environment set up with all dependencies
- ✓ Data available in `data/indibench_h5/` (train/val/test splits)
- ✓ Configuration file created for UNet model
- ✓ Baseline UNet model trained (100 epochs, 37 variables)
- ✓ ERA5-Land integration pipeline implemented (ready for deployment)

## Quick Start

### 1. Create directories

```bash
mkdir -p logs checkpoints
```

### 2. Test your setup first (recommended)

Before starting the long training, verify everything works:

```bash
sbatch scripts/test_setup.sbatch
```

This runs a quick 5-minute test. See [TESTING.md](TESTING.md) for details.

### 3. Train the UNet model

Once the test passes:

```bash
sbatch scripts/train_unet.sbatch
```

### 4. Monitor training

```bash
# Check job status
squeue -u $USER

# View training output
tail -f logs/train_unet_*.out
```

## What's the UNet Model?

The UNet is a convolutional neural network with encoder-decoder architecture commonly used in image-to-image tasks. For weather forecasting, it:
- Takes in 2 previous timesteps of weather data (256×256 grid, 37 variables)
- Predicts the next timestep (6 hours ahead)
- Uses skip connections between encoder and decoder
- Processes boundary conditions from coarser resolution data

## Configuration

The config file is at: `configs/boundary_forcing_unet.yaml`

Key settings:
- **Input**: 2 timesteps of 37 atmospheric variables
- **Output**: 1 timestep prediction (6 hours ahead)
- **Architecture**: 64 hidden channels, 3 resolution levels
- **Training**: 100 epochs, batch size 2, learning rate 2e-4
- **Data**: Your data in `data/indibench_h5/`

## File Structure

```
ML-Project/
├── IndiaWeatherBench/          # Original repository code
│   ├── train_boundary_forcing.py
│   ├── test_boundary_forcing.py
│   └── india_benchmark/        # Model implementations
├── data/indibench_h5/          # Your dataset
│   ├── train/                  # 2000-2017
│   ├── val/                    # 2018
│   └── test/                   # 2019
├── configs/
│   ├── boundary_forcing_unet.yaml   # UNet config
│   └── persistence.yaml             # Baseline config
├── scripts/
│   ├── train_unet.sbatch       # SLURM job for training
│   └── test_persistence.sbatch # Quick baseline test
├── checkpoints/                # Saved model checkpoints
└── logs/                       # Training logs
```

## Training Details

The UNet model will:
1. Load data from your `data/indibench_h5/` directory
2. Train for 100 epochs (can be changed in config)
3. Save checkpoints to `checkpoints/boundary_forcing_unet/`
4. Log metrics to wandb (offline mode by default)
5. Validate every epoch on 2018 data
6. Test on 2019 data after training

Expected training time: ~12-24 hours on a single GPU (depends on GPU type)

## After Training

Once training completes, your checkpoint will be at:
```
checkpoints/boundary_forcing_unet/last.ckpt
```

To evaluate the trained model, edit `scripts/test_unet.sbatch` to point to this checkpoint and run:
```bash
sbatch scripts/test_unet.sbatch
```

## Adjusting Training Parameters

Edit `scripts/train_unet.sbatch` and add command-line arguments:

```bash
# Reduce epochs for faster training
python train_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet.yaml \
    --trainer.max_epochs=50

# Reduce batch size if OOM
python train_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet.yaml \
    --data.batch_size=1

# Quick test run
python train_boundary_forcing.py \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet.yaml \
    --trainer.fast_dev_run=true
```

## ERA5-Land Integration (November 2025)

The project has been expanded to integrate soil moisture and land surface variables from ERA5-Land. This adds 6 new variables (soil moisture, heat fluxes, vegetation indices) to potentially improve forecast accuracy.

**Status**: Implementation complete, ready for data download and processing

**Key Documents**:
- [ERA5LAND_INTEGRATION.md](ERA5LAND_INTEGRATION.md) - Complete integration documentation
- [GEE_SETUP.md](GEE_SETUP.md) - Google Earth Engine setup instructions
- [archive_baseline_unet/BASELINE_METRICS.md](archive_baseline_unet/BASELINE_METRICS.md) - Baseline model performance

**Data Source**: Using Google Earth Engine instead of Copernicus CDS for more reliable downloads.

**Quick Start for ERA5-Land Integration**:
```bash
# 1. Authenticate with Google Earth Engine (see GEE_SETUP.md)
earthengine authenticate

# 2. Download ERA5-Land data via Google Earth Engine
sbatch scripts/download_era5_land_gee.sbatch

# 3. Process and integrate data
sbatch scripts/process_era5_land.sbatch

# 4. Update normalization parameters
sbatch scripts/compute_norm_params_era5land.sbatch

# 5. Validate integration
python scripts/validate_era5land_integration.py

# 6. Train with expanded dataset
sbatch scripts/train_unet_2gpu.sbatch \
    --config configs/boundary_forcing_unet_era5land.yaml \
    --trainer.devices=2
```

**Variables Added**:
- `swvl1`, `swvl2` - Soil moisture (layers 1 & 2)
- `slhf`, `sshf` - Surface latent & sensible heat flux
- `lai_hv`, `lai_lv` - Leaf area index (high & low vegetation)

Total variables: 37 (baseline) + 6 (ERA5-Land) = 43 variables

## Reference

- Paper: [IndiaWeatherBench: A Benchmark for Regional Weather Forecasting](https://arxiv.org/abs/2509.00653)
- Repository: https://github.com/tung-nd/IndiaWeatherBench
- ERA5-Land: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
