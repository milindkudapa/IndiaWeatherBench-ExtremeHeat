# Baseline UNet Model Performance Metrics

## Model Information

- **Model**: Boundary Forcing UNet
- **Architecture**: 36.1M parameters
  - Hidden channels: 64
  - Channel multipliers: [1, 2, 4]
  - Number of blocks: 2
  - Input channels: 74 (2 timesteps × 37 variables)
  - Output channels: 37 variables

- **Training Configuration**:
  - Epochs: 100
  - Batch size: 4
  - Learning rate: 2e-4
  - Optimizer: AdamW (β1=0.9, β2=0.95, weight_decay=1e-5)
  - Precision: bf16-mixed
  - Devices: 2 GPUs (A100)
  - Strategy: DDP

- **Dataset**:
  - Training: 2000-2017 (20,031 samples)
  - Validation: 2018 (1,460 samples)
  - Test: 2019 (1,460 samples)
  - Input variables: 37 atmospheric variables
  - Spatial resolution: 256×256 grid (~0.12° resolution)
  - Temporal resolution: 6-hourly (00, 06, 12, 18 UTC)

## Final Training Metrics (Epoch 99)

- **Training Loss**: 
  - `train/w_mse_agg`: 0.00107

- **Validation Loss**:
  - `val/w_mse_agg`: 0.0537

## Validation RMSE by Forecast Lead Time

### 6-hour Forecast (Single Step)
- 2m Temperature (TMP): 1.440 K
- 10m U-Wind (UGRD): 0.904 m/s
- 10m V-Wind (VGRD): 0.868 m/s
- MSLP (PRMSL): 71.60 Pa
- 500 hPa Geopotential Height (HGT500): 4.340 m
- 850 hPa Temperature (TMP_prl850): 0.676 K
- 500 hPa Temperature (TMP_prl500): 0.534 K
- 850 hPa U-Wind (UGRD_prl850): 1.110 m/s
- 500 hPa U-Wind (UGRD_prl500): 1.450 m/s
- 850 hPa V-Wind (VGRD_prl850): 1.060 m/s
- 500 hPa V-Wind (VGRD_prl500): 1.400 m/s
- 850 hPa Relative Humidity (RH850): 6.680 %
- 700 hPa Relative Humidity (RH700): 7.100 %
- 500 hPa Relative Humidity (RH500): 7.010 %

### 12-hour Forecast
- TMP: 1.870 K
- UGRD: 1.110 m/s
- VGRD: 1.050 m/s
- PRMSL: 93.30 Pa
- HGT500: 6.060 m

### 24-hour Forecast
- TMP: 2.420 K
- UGRD: 1.380 m/s
- VGRD: 1.280 m/s
- PRMSL: 134.0 Pa
- HGT500: 9.530 m

### 48-hour Forecast
- TMP: 3.290 K
- UGRD: 1.700 m/s
- VGRD: 1.560 m/s
- PRMSL: 183.0 Pa
- HGT500: 15.30 m

### 72-hour Forecast (3 days)
- TMP: 3.660 K
- UGRD: 1.910 m/s
- VGRD: 1.780 m/s
- PRMSL: 216.0 Pa
- HGT500: 19.10 m

## Checkpoint Files

- **Epoch 39 Checkpoint**: `epoch_039.ckpt` (414 MB)
- **Last Checkpoint**: `last.ckpt` (414 MB)

## Training Configuration Files

- `boundary_forcing_unet.yaml` - Main training configuration
- `config.yaml` - Lightning CLI configuration from training run

## Notes

This baseline model was trained on the IndiaWeatherBench dataset using only IMDAA atmospheric variables. Future work will integrate ERA5-Land soil moisture and land surface variables to potentially improve forecast accuracy, especially for near-surface variables and longer lead times.

## Archive Date

November 25, 2025


