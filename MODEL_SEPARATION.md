# Model Training Separation: Baseline vs ERA5-Land

This document tracks the complete separation between the baseline IWB model and the ERA5-Land expanded model.

---

## Model Comparison

| Component | Baseline Model | ERA5-Land Model |
|-----------|----------------|-----------------|
| **Config File** | `configs/boundary_forcing_unet.yaml` | `configs/boundary_forcing_unet_era5land.yaml` |
| **Training Script** | `scripts/train_unet_2gpu.sbatch` | `scripts/train_unet_era5land_2gpu.sbatch` |
| **Variables** | 37 (IWB only) | 45 (37 IWB + 6 ERA5-Land + 2 static) |
| **Input Channels** | 74 (2 × 37) | 90 (2 × 45) |
| **Output Channels** | 37 (1 × 37) | 45 (1 × 45) |

---

## Baseline Model (Already Trained)

### Configuration
- **Config**: `configs/boundary_forcing_unet.yaml`
- **Variables**: 37 IWB atmospheric variables
- **WandB Project**: `india_benchmark`
- **Checkpoints**: `checkpoints/` (default location)

### Training
- **Script**: `scripts/train_unet_2gpu.sbatch`
- **Status**: ✅ Already trained
- **Artifacts**: Preserved and unchanged

---

## ERA5-Land Model (New Training)

### Configuration
- **Config**: `configs/boundary_forcing_unet_era5land.yaml`
- **Variables**: 45 total
  - 37 IWB atmospheric variables (same as baseline)
  - 6 ERA5-Land surface variables (NEW):
    1. `swvl1` - Soil moisture layer 1 (0-7 cm)
    2. `swvl2` - Soil moisture layer 2 (7-28 cm)
    3. `slhf` - Surface latent heat flux
    4. `sshf` - Surface sensible heat flux
    5. `lai_hv` - Leaf area index (high vegetation)
    6. `lai_lv` - Leaf area index (low vegetation)
  - 2 static variables (LAND, MTERH)

### Training Setup
- **Script**: `scripts/train_unet_era5land_2gpu.sbatch` (NEW)
- **WandB Project**: `india_benchmark_era5land` (SEPARATE)
- **WandB Run Name**: `boundary_forcing_unet_era5land_45vars`
- **WandB Tags**: `['era5land', 'soil_moisture', 'heat_flux', 'lai', '45_variables']`
- **Checkpoints**: `checkpoints/boundary_forcing_unet_era5land/` (SEPARATE)
- **Status**: 🚀 Ready to train

---

## Complete Separation Checklist

### ✅ Configuration Files
- [x] Separate config files
- [x] Different checkpoint directories
- [x] Different WandB projects
- [x] Different run names

### ✅ Training Scripts
- [x] Separate SBATCH script (`train_unet_era5land_2gpu.sbatch`)
- [x] Different job names
- [x] Different log files
- [x] Explicit checkpoint directory specification

### ✅ Data & Normalization
- [x] Same data files (22,951 HDF5 with 49 variables)
- [x] Same normalization file (supports both models)
- [x] Each model uses subset of available variables

### ✅ Artifacts
- [x] Baseline checkpoints: `checkpoints/` (preserved)
- [x] ERA5-Land checkpoints: `checkpoints_era5land/` (completely separate directory)
- [x] Baseline wandb: `india_benchmark` project
- [x] ERA5-Land wandb: `india_benchmark_era5land` project
- [x] No checkpoint collision - models train independently

---

## Training Commands

### Baseline Model (Already Trained)
```bash
sbatch scripts/train_unet_2gpu.sbatch
```
**Do NOT run this again - baseline is already trained!**

### ERA5-Land Model (New Training)
```bash
sbatch scripts/train_unet_era5land_2gpu.sbatch
```

---

## Monitoring

### Baseline Model
- **WandB**: https://wandb.ai/YOUR_USERNAME/india_benchmark
- **Checkpoints**: `ML-Project/checkpoints/`
- **Logs**: Existing training logs

### ERA5-Land Model
- **WandB**: https://wandb.ai/YOUR_USERNAME/india_benchmark_era5land
- **Checkpoints**: `ML-Project/checkpoints/boundary_forcing_unet_era5land/`
- **Logs**: `logs/train_unet_era5land_<JOB_ID>.out`
- **Monitor**: `tail -f logs/train_unet_era5land_<JOB_ID>.out`

---

## Expected Outcomes

### Research Questions
1. **Do ERA5-Land variables improve weather forecasts?**
   - Compare forecast skill metrics between baseline and ERA5-Land models
   
2. **Which variables contribute most?**
   - Analyze impact of soil moisture vs heat fluxes vs LAI
   
3. **Where do improvements occur?**
   - Spatial analysis: regions with vegetation vs arid areas
   - Temporal analysis: monsoon season vs dry season
   
4. **What forecast lead times benefit?**
   - Short-term (6-24h) vs medium-range (2-7 days)

### Evaluation Plan
- Train ERA5-Land model to convergence
- Compare validation metrics (RMSE, ACC, etc.)
- Run full test set evaluation (2019)
- Generate comparison plots and statistics
- Document findings

---

## Key Differences Summary

| Aspect | Impact |
|--------|--------|
| **More variables** | +8 variables gives model more surface information |
| **Soil moisture** | May improve temperature and precipitation forecasts |
| **Heat fluxes** | Better surface-atmosphere coupling |
| **Vegetation** | Seasonal and spatial information for land regions |
| **Larger model** | +16 input channels → slightly more parameters |

---

## File Organization

```
ML-Project/
├── configs/
│   ├── boundary_forcing_unet.yaml              # Baseline (37 vars)
│   └── boundary_forcing_unet_era5land.yaml     # ERA5-Land (45 vars)
├── scripts/
│   ├── train_unet_2gpu.sbatch                  # Baseline training
│   └── train_unet_era5land_2gpu.sbatch         # ERA5-Land training (NEW)
├── checkpoints/
│   ├── (baseline model checkpoints)            # Preserved
│   └── boundary_forcing_unet_era5land/         # New ERA5-Land checkpoints
├── logs/
│   ├── train_unet_2gpu_*.out                   # Baseline logs
│   └── train_unet_era5land_*.out               # ERA5-Land logs
└── data/
    └── indibench_h5/                           # Shared dataset (49 vars)
        ├── train/ (20,031 files)
        ├── val/ (1,460 files)
        └── test/ (1,460 files)
```

---

## Notes

- **No interference**: Baseline model artifacts are completely preserved
- **Same data**: Both models use same HDF5 files, just different variable subsets
- **Independent tracking**: Separate WandB projects for easy comparison
- **Easy comparison**: Can load both models and compare predictions side-by-side

---

**Last Updated**: December 1, 2025  
**Status**: ERA5-Land model ready for training

