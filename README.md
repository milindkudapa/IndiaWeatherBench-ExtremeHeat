# IndiaWeatherBench UNet with ERA5-Land Integration

Regional weather forecasting UNET model for India, integrating ERA5-Land soil moisture and land surface variables.

---

## Current Status

✅ **Baseline Model Trained** (100 epochs, 37 variables)  
✅ **ERA5-Land Data Downloaded** (CDS, 2000-2019, 6 variables)  
⏳ **Next: Integrate ERA5-Land into IWB Dataset**

---

## Quick Start: ERA5-Land Integration

### Step 1: Process ERA5-Land Data (~6-12 hours)
```bash
sbatch scripts/process_era5_land_netcdf.sbatch
```
Extracts NetCDF files, regrids to IWB grid, adds 6 variables to HDF5 files.

### Step 2: Compute Normalization (~2-4 hours)
```bash
sbatch scripts/compute_norm_params_era5land.sbatch
```
Computes statistics for new variables, updates `norm_params.json`.

### Step 3: Validate Integration (~5 min)
```bash
python scripts/validate_era5land_integration.py \
    --h5-dir data/indibench_h5 \
    --norm-params data/indibench_h5/norm_params.json
```
Verifies all data integrated correctly.

### Step 4: Train Expanded Model
```bash
sbatch scripts/train_unet_2gpu.sbatch  # Update to use new config
```
Uses `configs/boundary_forcing_unet_era5land.yaml` (43 variables).

---

## Project Structure

```
ML-Project/
├── configs/
│   ├── boundary_forcing_unet.yaml          # Baseline (37 vars)
│   └── boundary_forcing_unet_era5land.yaml # Expanded (43 vars)
├── scripts/
│   ├── train_unet_2gpu.sbatch              # Training job
│   ├── test_unet.sbatch                    # Evaluation
│   ├── test_persistence.sbatch             # Baseline test
│   ├── download_era5_land_hourly.py        # CDS download (complete)
│   ├── download_era5_land_hourly_cds.sbatch
│   ├── process_era5_land_netcdf.sbatch     # Integration (step 1)
│   ├── compute_norm_params_era5land.py     # Normalization (step 2)
│   ├── compute_norm_params_era5land.sbatch
│   └── validate_era5land_integration.py    # Validation (step 3)
├── data/
│   ├── indibench_h5/        # IWB dataset (HDF5 files)
│   └── era5_land_cds/       # ERA5-Land data (NetCDF, 240 files)
├── archive_baseline_unet/   # Baseline model & metrics
├── checkpoints/             # Model checkpoints
└── logs/                    # SLURM logs
```

---

## Data Overview

### IndiaWeatherBench (IWB)
- **Domain**: 6-37°N, 66-97°E
- **Resolution**: 0.12° (~12 km), 256×256 grid
- **Temporal**: 6-hourly (00, 06, 12, 18 UTC)
- **Period**: 2000-2019 (train: 2000-2017, val: 2018, test: 2019)
- **Variables**: 37 atmospheric variables
- **Format**: HDF5 (one file per timestep)

### ERA5-Land
- **Resolution**: 0.1° (~10 km), 321×321 grid
- **Temporal**: 6-hourly (matches IWB)
- **Period**: 2000-2019
- **Variables**: 6 land surface variables
  - `swvl1`, `swvl2` - Soil moisture (0-7 cm, 7-28 cm)
  - `slhf`, `sshf` - Latent & sensible heat flux
  - `lai_hv`, `lai_lv` - Leaf area index (high/low vegetation)
- **Format**: ZIP-compressed NetCDF (240 monthly files)

---

## Model Details

### Baseline UNet (37 variables)
- **Input**: 2 timesteps × 37 variables = 74 channels
- **Output**: 1 timestep, 6 hours ahead
- **Architecture**: 64 hidden channels, 3 resolution levels
- **Performance**: See `archive_baseline_unet/BASELINE_METRICS.md`

### Expanded UNet (43 variables)
- **Input**: 2 timesteps × 43 variables = 86 channels
- **Variables**: 37 (IWB) + 6 (ERA5-Land)
- **Architecture**: Same (auto-adjusts to input channels)

---

## Monitoring Jobs

```bash
# Check job status
squeue -u $USER

# View logs
tail -f logs/process_era5_netcdf_<job_id>.out
tail -f logs/compute_norm_era5_<job_id>.out
tail -f logs/train_unet_2gpu_<job_id>.out

# Check specific errors
tail -f logs/process_era5_netcdf_<job_id>.err
```

---

## References

- **Paper**: [IndiaWeatherBench: A Benchmark for Regional Weather Forecasting](https://arxiv.org/abs/2509.00653)
- **Repository**: https://github.com/tung-nd/IndiaWeatherBench
- **ERA5-Land**: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
