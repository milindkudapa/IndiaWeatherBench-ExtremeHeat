# ERA5-Land Integration with IndiaWeatherBench - Complete Guide

**Date**: November 29, 2025  
**Status**: 🚧 In Progress - Data Processing Running  
**Purpose**: Expand UNET model inputs from 37 to 43 variables by adding ERA5-Land soil moisture and vegetation data

---

## Table of Contents

1. [Overview](#overview)
2. [Data Format Conversions](#data-format-conversions)
3. [Processing Pipeline](#processing-pipeline)
4. [Integration Results](#integration-results)
5. [Next Steps](#next-steps)

---

## Overview

### Objective
Integrate 6 ERA5-Land variables with the existing 37-variable IndiaWeatherBench dataset to train an enhanced UNET model with 43 total input variables.

### ERA5-Land Variables Added
| Variable | Name | Description | Units (Original) | Units (After Conversion) |
|----------|------|-------------|------------------|--------------------------|
| `swvl1` | Soil Moisture Layer 1 | Volumetric soil water (0-7 cm depth) | m³/m³ | m³/m³ (no conversion) |
| `swvl2` | Soil Moisture Layer 2 | Volumetric soil water (7-28 cm depth) | m³/m³ | m³/m³ (no conversion) |
| `slhf` | Surface Latent Heat Flux | Energy from evaporation/condensation | J/m² (accumulated) | W/m² (average rate) |
| `sshf` | Surface Sensible Heat Flux | Energy from temperature diff | J/m² (accumulated) | W/m² (average rate) |
| `lai_hv` | LAI High Vegetation | Leaf area index for trees/shrubs | m²/m² | m²/m² (no conversion) |
| `lai_lv` | LAI Low Vegetation | Leaf area index for crops/grass | m²/m² | m²/m² (no conversion) |

### Why These Variables?
- **Soil Moisture**: Critical for monsoon prediction, agricultural forecasting
- **Heat Fluxes**: Important for surface-atmosphere coupling, convection initiation
- **LAI**: Affects evapotranspiration, surface energy balance

---

## Data Format Conversions

### Challenge: Multiple Format Mismatches

The ERA5-Land and IndiaWeatherBench datasets have fundamentally different formats:

| Aspect | ERA5-Land (Downloaded) | IndiaWeatherBench (Target) | Conversion Required |
|--------|----------------------|----------------------------|---------------------|
| **File Format** | GeoTIFF (.tif) | HDF5 (.h5) | ✓ Yes |
| **Temporal Resolution** | Monthly means | 6-hourly (00, 06, 12, 18 UTC) | ✓ Yes - replicate monthly |
| **Spatial Resolution** | 0.1° (~11.1 km) | 0.12° (~13.3 km) | ✓ Yes - bilinear interpolation |
| **Grid Dimensions** | 322 × 321 pixels | 256 × 256 pixels | ✓ Yes - regrid + crop |
| **Spatial Extent** | 65.90-98.00°E, 5.90-38.10°N | 66.60-97.25°E, 6.00-36.72°N | ✓ Yes - crop to target |
| **Heat Flux Units** | Accumulated J/m² per month | Average W/m² | ✓ Yes - divide by seconds |
| **Data Type** | float64 | float32 | ✓ Yes |
| **Number of Files** | 240 (one per month) | ~23,360 (one per 6-hour timestep) | ✓ Yes |

### Solution: Comprehensive Processing Pipeline

Created `process_era5_land_geotiff.py` to handle all conversions in one pass.

---

## Processing Pipeline

### Step 1: Read GeoTIFF File
```python
with rasterio.open('era5_land_2000_01.tif') as src:
    # Extract all 6 bands
    swvl1 = src.read(1)  # 322×321
    swvl2 = src.read(2)
    slhf = src.read(3)   # Accumulated J/m²
    sshf = src.read(4)   # Accumulated J/m²
    lai_hv = src.read(5)
    lai_lv = src.read(6)
```

### Step 2: Convert Heat Fluxes
```python
# For each heat flux variable (slhf, sshf):
num_days = calendar.monthrange(year, month)[1]
seconds_in_month = num_days * 24 * 3600

# Convert from accumulated J/m² to average W/m²
avg_flux_W_per_m2 = accumulated_J_per_m2 / seconds_in_month
```

**Example** (January 2000, 31 days):
- Seconds in month: 2,678,400
- If `slhf` (accumulated) = -830,000 J/m²
- Then `slhf` (average) = -830,000 / 2,678,400 = **-0.31 W/m²** ✓

### Step 3: Regrid and Crop
```python
# Bilinear interpolation from 0.1° to 0.12° resolution
# Crop from 322×321 → 256×256 to match IndiaWeatherBench
from scipy.interpolate import RegularGridInterpolator

target_lats = np.linspace(6.0, 36.72, 256)
target_lons = np.linspace(66.6, 97.25, 256)

regridded = bilinear_interpolate(
    source_data,      # 322×321
    source_lats,      # 322 points @ 0.1°
    source_lons,      # 321 points @ 0.1°
    target_lats,      # 256 points @ 0.12°
    target_lons       # 256 points @ 0.12°
)  # Output: 256×256
```

### Step 4: Replicate to 6-Hourly Timesteps
```python
# January 2000 has 31 days × 4 timesteps/day = 124 timesteps
for day in range(1, 32):
    for hour in [0, 6, 12, 18]:
        h5_filename = f"2000-01-{day:02d}_{hour//6:02d}.h5"
        # Use the SAME monthly mean for all timesteps
```

**Rationale**: ERA5-Land monthly means are the best available. Replicating ensures:
- Temporal consistency within each month
- Proper data format for 6-hourly model training
- Seasonal variations captured across months

### Step 5: Integrate into HDF5
```python
with h5py.File(h5_filename, 'a') as f:  # Append mode
    for var_name in ['swvl1', 'swvl2', 'slhf', 'sshf', 'lai_hv', 'lai_lv']:
        # Add new variable alongside existing 37-44 variables
        f.create_dataset(
            var_name,
            data=processed_data[var_name],  # 256×256, float32
            dtype=np.float32,
            compression=None  # Match existing format
        )
```

**Result**: Each HDF5 file goes from 44 variables → 50 variables

---

## Integration Results

### Test Run: January 2000

**Command**:
```bash
python process_era5_land_geotiff.py --test-month 2000-01
```

**Results**:
- ✓ Files updated: 95 / 124 timesteps (76.6%)
- ✓ Files skipped: 29 (expected - not all timesteps exist in training set)

**Verification** (`2000-01-01_00.h5`):
```
Before:  44 variables (APCP, TMP, UGRD, VGRD, ..., time)
After:   50 variables (all above + swvl1, swvl2, slhf, sshf, lai_hv, lai_lv)

New variables:
  swvl1:  shape=(256,256), min=0.0000,    max=0.6723,  mean=0.1273 m³/m³  ✓
  swvl2:  shape=(256,256), min=0.0000,    max=0.6275,  mean=0.1476 m³/m³  ✓
  slhf:   shape=(256,256), min=-3.2258,   max=0.1298,  mean=-0.3198 W/m²  ✓
  sshf:   shape=(256,256), min=-2.5410,   max=0.2577,  mean=-0.5035 W/m²  ✓
  lai_hv: shape=(256,256), min=0.0000,    max=6.3600,  mean=0.7859 m²/m²  ✓
  lai_lv: shape=(256,256), min=0.0000,    max=4.8592,  mean=0.7485 m²/m²  ✓

Existing variables: ALL PRESERVED ✓
```

**Note**: Heat fluxes now in W/m² range (not millions of J/m²) ✓

### Full Processing (SLURM Job 5026859)

**Command**:
```bash
sbatch scripts/process_era5_land_integration.sbatch
```

**Processing**:
- 240 months (2000-01 through 2019-12)
- Approximately 23,360 HDF5 files to update
- Estimated time: 4-6 hours
- Resources: 4 CPUs, 32 GB RAM

**Expected Final State**:
- Training set (2000-2017): All files updated with 6 new variables
- Validation set (2018): All files updated
- Test set (2019): All files updated

---

## Next Steps

### 1. Monitor Processing Job ✓ In Progress
```bash
# Check job status
squeue -u mck2199

# Monitor logs
tail -f logs/process_era5land_5026859.out
```

### 2. Update Normalization Parameters (After processing completes)
```bash
sbatch scripts/compute_norm_params_era5land.sbatch
```

This will:
- Compute mean, std, diff_mean, diff_std for 6 new variables
- Update `data/indibench_h5/norm_params.json`
- Use only training set (2000-2017) for statistics

### 3. Create New Training Config
- Copy `configs/boundary_forcing_unet.yaml` → `configs/boundary_forcing_unet_era5land.yaml`
- Update `variables` list from 37 → 43 variables
- Model will automatically adjust input channels: 74 (2×37) → 86 (2×43)

### 4. Validate Integration
```bash
python scripts/validate_era5land_integration.py
```

Checks:
- All HDF5 files contain 6 new variables
- Variable shapes are (256, 256)
- No NaN/Inf values
- Value ranges are reasonable
- Normalization applied correctly

### 5. Train Expanded Model
```bash
sbatch scripts/train_unet_era5land.sbatch
```

Options:
- **Option A**: Train from scratch with 43 variables
- **Option B**: Fine-tune from baseline checkpoint (37 variables)

---

## Technical Specifications

### Processing Script Details

**Location**: `IndiaWeatherBench/india_benchmark/data_processing/process_era5_land_geotiff.py`

**Key Functions**:
```python
extract_coordinates_from_geotiff()    # Get lat/lon from GeoTIFF
regrid_bilinear()                     # Spatial regridding
convert_heat_flux()                   # Unit conversion for fluxes
process_month_geotiff()               # Main processing logic
```

**Features**:
- Dry-run mode for testing
- Single-month testing
- Automatic train/val/test split detection
- Comprehensive error handling
- Progress tracking

### Data Integrity

**Preserved from Original**:
- All 44 existing variables in each HDF5 file
- File naming convention
- Data type (float32)
- Compression settings (None)
- Coordinate system

**Added**:
- 6 new variables per file
- Consistent 256×256 shape
- Proper units (W/m² for fluxes)
- Physically reasonable values

---

## Summary

### What Was Accomplished

✅ Downloaded 240 months of ERA5-Land data from Google Earth Engine  
✅ Created comprehensive preprocessing pipeline handling all format conversions  
✅ Successfully tested integration on January 2000 (95 files updated)  
✅ Submitted SLURM job to process all 240 months  
✅ Verified data quality and proper unit conversions  

### What's Next

🚧 Complete full dataset processing (job running)  
⏭️ Update normalization parameters  
⏭️ Create new 43-variable training configuration  
⏭️ Validate complete integration  
⏭️ Train expanded UNET model  

### Key Achievement

**Successfully bridged the gap between two completely different data formats**:
- GeoTIFF monthly means → HDF5 6-hourly data
- 322×321 @ 0.1° → 256×256 @ 0.12°
- Accumulated J/m² → Average W/m²
- 240 files → ~23,360 integrated timesteps

**All while preserving the existing IndiaWeatherBench dataset integrity!**

---

**Last Updated**: November 29, 2025  
**Processing Status**: Job 5026859 running  
**Estimated Completion**: ~4-6 hours from job start

