# ERA5-Land Data Integration with IndiaWeatherBench

## Overview

This document describes the integration of ERA5-Land soil moisture and land surface variables into the IndiaWeatherBench UNET weather forecasting model. The integration expands the model's input features from 37 atmospheric variables to 43 total variables, adding 6 land surface variables from the ERA5-Land dataset.

**Date**: November 25, 2025  
**Status**: Implementation complete, ready for data download and processing

## Variables Added

The following ERA5-Land variables have been integrated:

1. **swvl1**: Volumetric soil water layer 1 (0-7 cm depth)
   - Units: m³/m³
   - Typical range: 0.0 - 0.6
   - Sampling: Instantaneous values at 6-hourly intervals

2. **swvl2**: Volumetric soil water layer 2 (7-28 cm depth)
   - Units: m³/m³
   - Typical range: 0.0 - 0.6
   - Sampling: Instantaneous values at 6-hourly intervals

3. **slhf**: Surface latent heat flux
   - Units: W/m²
   - Typical range: -500 to 500
   - Sampling: Mean over 6-hour windows

4. **sshf**: Surface sensible heat flux
   - Units: W/m²
   - Typical range: -300 to 300
   - Sampling: Mean over 6-hour windows

5. **lai_hv**: Leaf area index, high vegetation
   - Units: m²/m²
   - Typical range: 0.0 - 10.0
   - Sampling: Instantaneous values at 6-hourly intervals

6. **lai_lv**: Leaf area index, low vegetation
   - Units: m²/m²
   - Typical range: 0.0 - 10.0
   - Sampling: Instantaneous values at 6-hourly intervals

## Data Specifications

### Spatial Coverage
- Domain: 6°N - 36.72°N, 66.6°E - 97.25°E (India subcontinent)
- Grid size: 256 × 256
- Native ERA5-Land resolution: ~0.1° (~9 km)
- Target IndiaWeatherBench resolution: ~0.12° (~12 km)
- Regridding method: Bilinear interpolation

### Temporal Coverage
- Time period: 2000-01-01 to 2019-12-31
- Native ERA5-Land resolution: Hourly
- Target resolution: 6-hourly (00, 06, 12, 18 UTC)
- Aggregation method: 
  - Fluxes (slhf, sshf): Mean over 6-hour windows
  - Others: Instantaneous values at 6-hourly intervals

### Data Splits
- **Training**: 2000-2017 (20,031 timesteps)
- **Validation**: 2018 (1,460 timesteps)
- **Test**: 2019 (1,460 timesteps)

## Implementation Steps

### Phase 1: Baseline Preservation ✅

All baseline work has been archived:
- Model checkpoints: `archive_baseline_unet/checkpoints/`
- Configuration files: `archive_baseline_unet/configs/`
- Training logs: `archive_baseline_unet/logs/`
- Performance metrics: `archive_baseline_unet/BASELINE_METRICS.md`

### Phase 2: Data Acquisition Setup ✅

**Prerequisites**:
- CDS API installed: `uv pip install cdsapi`
- CDS API credentials configured: `~/.cdsapirc`
- See `CDS_API_SETUP.md` for detailed instructions

**Scripts Created**:
- `scripts/download_era5_land.py`: Python script to download ERA5-Land data
- `scripts/download_era5_land.sbatch`: SLURM job for downloading

**To Download Data**:
```bash
# After setting up CDS credentials
sbatch scripts/download_era5_land.sbatch
```

Expected download time: 6-12 hours for 20 years of data.

### Phase 3: Data Preprocessing ✅

**Scripts Created**:
- `IndiaWeatherBench/india_benchmark/data_processing/process_era5_land.py`: 
  Main preprocessing script that handles:
  - Loading ERA5-Land NetCDF files
  - Spatial regridding (0.1° → 0.12°)
  - Cropping to IndiaWeatherBench domain
  - Temporal aggregation (hourly → 6-hourly)
  - Converting to HDF5 and adding to existing files

- `scripts/process_era5_land.sbatch`: SLURM job for preprocessing

**Processing Pipeline**:
1. Load ERA5-Land NetCDF files (one per year)
2. Regrid from 0.1° to 0.12° using bilinear interpolation
3. Crop to exact IndiaWeatherBench grid (256×256)
4. Aggregate hourly data to 6-hourly intervals:
   - Fluxes: Average over 6-hour windows
   - State variables: Instantaneous at 00/06/12/18 UTC
5. Add variables to existing HDF5 files using `h5py` append mode
6. Maintain dtype=float32, no compression (consistent with existing data)

**To Process Data**:
```bash
# After downloading ERA5-Land data
sbatch scripts/process_era5_land.sbatch
```

Expected processing time: 4-8 hours with parallelization.

### Phase 4: Normalization Parameters ✅

**Scripts Created**:
- Reuses existing: `scripts/compute_norm_params_modified.py`
- `scripts/compute_norm_params_era5land.sbatch`: SLURM job

**Process**:
1. Script automatically detects all variables in HDF5 files
2. Computes mean, std, diff_mean, diff_std for each variable
3. Uses training split only (2000-2017)
4. Backs up existing `norm_params.json` before updating
5. Generates new `norm_params.json` with all 43 variables

**To Compute Normalization**:
```bash
# After processing ERA5-Land data
sbatch scripts/compute_norm_params_era5land.sbatch
```

Expected computation time: 1-2 hours.

### Phase 5: Model Configuration ✅

**New Configuration File**:
- `configs/boundary_forcing_unet_era5land.yaml`

**Key Changes from Baseline**:
- Variables list expanded from 37 to 43
- Input channels: 74 (2×37) → 86 (2×43)
- Checkpoint directory: `boundary_forcing_unet_era5land`
- Logger name: `boundary_forcing_unet_era5land`
- Added ERA5-Land variables to `vars_to_log` for monitoring

**Model Architecture**:
- No changes needed - UNet dynamically adapts to input channel count
- `in_channels = n_input_steps * len(variables) = 2 × 43 = 86`

### Phase 6: Validation ✅

**Validation Script**:
- `scripts/validate_era5land_integration.py`

**Checks Performed**:
1. Verify all HDF5 files contain ERA5-Land variables
2. Check shape consistency (256×256)
3. Detect NaN or inf values
4. Verify reasonable value ranges
5. Test dataloader with new configuration
6. Confirm normalization parameters

**To Validate Integration**:
```bash
# After all processing steps
cd /burg-archive/home/mck2199/ML-Project
source venv/bin/activate
python scripts/validate_era5land_integration.py \
    --data-dir data/indibench_h5 \
    --config configs/boundary_forcing_unet_era5land.yaml
```

## File Structure

```
ML-Project/
├── archive_baseline_unet/           # Baseline model archive
│   ├── checkpoints/
│   │   ├── epoch_039.ckpt (414 MB)
│   │   └── last.ckpt (414 MB)
│   ├── configs/
│   │   ├── boundary_forcing_unet.yaml
│   │   └── config.yaml
│   ├── logs/
│   └── BASELINE_METRICS.md
│
├── configs/
│   ├── boundary_forcing_unet.yaml           # Original config (37 vars)
│   └── boundary_forcing_unet_era5land.yaml  # New config (43 vars)
│
├── data/
│   ├── era5_land_raw/                       # Downloaded NetCDF files
│   │   ├── era5_land_2000.nc
│   │   ├── era5_land_2001.nc
│   │   └── ... (2019.nc)
│   └── indibench_h5/                        # HDF5 files (updated)
│       ├── norm_params.json                 # Updated with ERA5-Land vars
│       ├── norm_params_backup_*.json        # Backup of original
│       ├── train/ (20,031 files)
│       ├── val/ (1,460 files)
│       └── test/ (1,460 files)
│
├── scripts/
│   ├── download_era5_land.py
│   ├── download_era5_land.sbatch
│   ├── process_era5_land.sbatch
│   ├── compute_norm_params_era5land.sbatch
│   └── validate_era5land_integration.py
│
├── IndiaWeatherBench/
│   └── india_benchmark/
│       └── data_processing/
│           └── process_era5_land.py
│
├── CDS_API_SETUP.md                         # CDS API setup instructions
└── ERA5LAND_INTEGRATION.md                  # This document
```

## Training with Expanded Dataset

Once data processing is complete and validation passes:

### Option 1: Train from Scratch
```bash
sbatch scripts/train_unet_2gpu.sbatch \
    --config /burg-archive/home/mck2199/ML-Project/configs/boundary_forcing_unet_era5land.yaml \
    --trainer.devices=2 \
    --data.batch_size=4
```

### Option 2: Fine-tune from Baseline

To fine-tune from the baseline checkpoint:

1. Modify the training script to load checkpoint
2. Note: Input dimensions changed (74 → 86 channels), so only compatible layers can be loaded
3. May need to initialize new input projection layer

### Monitoring Training

- Checkpoints saved to: `checkpoints/boundary_forcing_unet_era5land/`
- WandB project: `india_benchmark`
- Run name: `boundary_forcing_unet_era5land`

## Expected Benefits

Adding ERA5-Land variables may improve:

1. **Near-surface predictions**: Soil moisture and heat fluxes directly influence near-surface temperature and humidity
2. **Longer lead times**: Land surface memory can improve forecasts beyond 24-48 hours
3. **Monsoon predictions**: Soil moisture is crucial for monsoon onset and intensity
4. **Regional variations**: Vegetation indices capture land-atmosphere coupling differences

## Troubleshooting

### CDS API Issues
- **Invalid API key**: Check `~/.cdsapirc` formatting
- **Terms not accepted**: Visit ERA5-Land dataset page and accept license
- **Slow downloads**: CDS servers can be congested; try off-peak hours

### Processing Issues
- **Memory errors**: Reduce number of workers or increase memory allocation
- **Missing variables**: Check ERA5-Land variable names in NetCDF files
- **Shape mismatches**: Verify spatial domain extraction is correct

### Validation Issues
- **Missing ERA5-Land vars**: Preprocessing may not have completed for all files
- **NaN values**: Check ERA5-Land data quality, may need interpolation
- **Range issues**: Some variables may have outliers, check against ERA5-Land documentation

### Training Issues
- **OOM errors**: Reduce batch size (43 vars = more memory than 37 vars)
- **Slow convergence**: May need to adjust learning rate or warmup schedule
- **NaN loss**: Check normalization statistics are reasonable for new variables

## Technical Notes

### Data Format Compatibility
- ERA5-Land (NetCDF) → HDF5: Handled by `process_era5_land.py`
- All processing done in memory-efficient chunks
- No changes needed to existing dataloader code

### Spatial Regridding Details
- Method: Bilinear interpolation via `scipy.interpolate.RegularGridInterpolator`
- Source: ERA5-Land 0.1° grid
- Target: IndiaWeatherBench 0.12° grid (256×256)
- Ensures consistency with existing IMDAA variables

### Temporal Aggregation Details
- **Flux variables** (slhf, sshf):
  - Hourly accumulations averaged over 6-hour windows
  - Window: (target_time - 6h) to target_time
  - Captures the average flux over the period

- **State variables** (swvl1, swvl2, lai_hv, lai_lv):
  - Instantaneous values at 00, 06, 12, 18 UTC
  - Matches timestamp of other atmospheric variables

### Storage Requirements
- Raw ERA5-Land NetCDF: ~50-100 GB (20 years, 6 variables)
- Updated HDF5 files: ~2 MB additional per file (~46 GB total increase)
- Total additional storage: ~150 GB

## References

1. **IndiaWeatherBench Paper**: https://arxiv.org/abs/2509.00653
2. **ERA5-Land Documentation**: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
3. **CDS API Documentation**: https://cds.climate.copernicus.eu/how-to-api
4. **Baseline Model Archive**: `archive_baseline_unet/BASELINE_METRICS.md`

## Contact

For questions or issues with the integration:
- Check validation script output first
- Review this documentation
- Examine log files in `logs/` directory

## Change Log

- **2025-11-25**: Initial integration implementation
  - Created all data pipeline scripts
  - Updated configuration files
  - Documented process
  - Ready for data download and processing


