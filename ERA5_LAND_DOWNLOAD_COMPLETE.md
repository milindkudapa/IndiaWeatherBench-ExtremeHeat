# ERA5-Land Download - FINAL SANITY CHECK ✓

**Date**: November 29, 2025  
**Status**: ✅ **COMPLETE AND VALIDATED**  
**Data Source**: Google Earth Engine (GEE)

---

## 🎉 Download Status: 100% COMPLETE

### Summary
- **Total Files**: 240 / 240 months ✓
- **Coverage**: 2000-01 through 2019-12 (20 years)
- **Total Size**: 427 MB (~1.78 MB per file)
- **Format**: GeoTIFF (multi-band, 6 variables per file)
- **Missing Data**: NONE

---

## ✅ Data Completeness

### By Year
| Year | Months | Status | Purpose |
|------|--------|--------|---------|
| 2000 | 12/12 | ✓ Complete | Training |
| 2001 | 12/12 | ✓ Complete | Training |
| 2002 | 12/12 | ✓ Complete | Training |
| 2003 | 12/12 | ✓ Complete | Training |
| 2004 | 12/12 | ✓ Complete | Training |
| 2005 | 12/12 | ✓ Complete | Training |
| 2006 | 12/12 | ✓ Complete | Training |
| 2007 | 12/12 | ✓ Complete | Training |
| 2008 | 12/12 | ✓ Complete | Training |
| 2009 | 12/12 | ✓ Complete | Training |
| 2010 | 12/12 | ✓ Complete | Training |
| 2011 | 12/12 | ✓ Complete | Training |
| 2012 | 12/12 | ✓ Complete | Training |
| 2013 | 12/12 | ✓ Complete | Training |
| 2014 | 12/12 | ✓ Complete | Training |
| 2015 | 12/12 | ✓ Complete | Training |
| 2016 | 12/12 | ✓ Complete | Training |
| 2017 | 12/12 | ✓ Complete | Validation |
| 2018 | 12/12 | ✓ Complete | Validation |
| 2019 | 12/12 | ✓ Complete | Test |
| **TOTAL** | **240/240** | **✓ COMPLETE** | **All splits** |

### By Data Split
- **Training** (2000-2016): 204/204 months ✓
- **Validation** (2017-2018): 24/24 months ✓
- **Test** (2019): 12/12 months ✓

---

## ✅ File Structure Validation

### Spatial Properties
- **Dimensions**: 322 × 321 pixels
- **Resolution**: 0.1° per pixel (~11.1 km)
- **Coordinate System**: EPSG:4326 (WGS84)
- **Bounds**: [65.90°E, 5.90°N, 98.00°E, 38.10°N]
- **Coverage**: ✓ Fully covers IndiaWeatherBench region (66.6-97.25°E, 6-36.72°N)

### File Format
- **Format**: GeoTIFF (.tif)
- **Bands per file**: 6
- **Data type**: float64 (will convert to float32 during preprocessing)
- **File size range**: 1.68 - 1.82 MB (consistent!)
- **Average file size**: 1.78 MB

---

## ✅ Variable Validation

### Band Mapping (verified from GEE)
| Band | Variable | Full Name | Units |
|------|----------|-----------|-------|
| 1 | `swvl1` | volumetric_soil_water_layer_1 | m³/m³ |
| 2 | `swvl2` | volumetric_soil_water_layer_2 | m³/m³ |
| 3 | `slhf` | surface_latent_heat_flux | J/m² (accumulated) |
| 4 | `sshf` | surface_sensible_heat_flux | J/m² (accumulated) |
| 5 | `lai_hv` | leaf_area_index_high_vegetation | m²/m² |
| 6 | `lai_lv` | leaf_area_index_low_vegetation | m²/m² |

### Variable Ranges (across all 240 months)

**Soil Moisture (volumetric):**
- `swvl1` (Layer 1, 0-7 cm): 0.00 - 0.75 m³/m³ ✓
- `swvl2` (Layer 2, 7-28 cm): 0.00 - 0.76 m³/m³ ✓

**Heat Fluxes (accumulated):**
- `slhf`: -11.9M to +1.6M J/m² ⚠️ Need conversion to W/m²
- `sshf`: -9.6M to +5.3M J/m² ⚠️ Need conversion to W/m²

**Leaf Area Index:**
- `lai_hv` (High Vegetation): 0.00 - 6.48 m²/m² ✓
- `lai_lv` (Low Vegetation): 0.00 - 5.03 m²/m² ✓

### Data Quality
- **NaN values**: NONE (0 across all 240 files)
- **Inf values**: NONE
- **Valid pixels**: 100% in all files
- **Temporal consistency**: ✓ All files have same dimensions and structure
- **Size consistency**: ✓ All files within 1.68-1.82 MB range

---

## ⚠️ Preprocessing Notes

### Heat Flux Conversion Required
The heat flux variables (`slhf`, `sshf`) are **accumulated values** over the month in J/m², not instantaneous rates in W/m².

**During preprocessing**, we need to:
1. Calculate the number of seconds in each month
2. Divide accumulated values by seconds to get average W/m²
3. Formula: `flux_W_per_m2 = accumulated_J_per_m2 / seconds_in_month`

Example for January (31 days):
- Seconds in month: 31 × 24 × 3600 = 2,678,400 seconds
- If accumulated slhf = -830,000 J/m²
- Average slhf = -830,000 / 2,678,400 = -0.31 W/m²

### Spatial Regridding Required
- **Current**: 322 × 321 @ 0.1° resolution
- **Target**: 256 × 256 @ 0.12° resolution (IndiaWeatherBench grid)
- **Method**: Bilinear interpolation + cropping

### Temporal Alignment
- **Downloaded**: Monthly means
- **Target**: 6-hourly timesteps (00, 06, 12, 18 UTC)
- **Strategy**: Repeat monthly mean for all 6-hourly timesteps in that month

---

## 📊 Sample Data Statistics

### January 2000 (Representative Sample)
| Variable | Min | Max | Mean | Median | Std Dev |
|----------|-----|-----|------|--------|---------|
| swvl1 | 0.000 | 0.677 | 0.127 | 0.112 | 0.133 |
| swvl2 | 0.000 | 0.673 | 0.148 | 0.155 | 0.136 |
| slhf | -9.4M | 425k | -830k | -224k | 1.21M |
| sshf | -7.0M | 732k | -1.31M | -798k | 1.46M |
| lai_hv | 0.000 | 6.482 | 0.775 | 0.000 | 1.381 |
| lai_lv | 0.000 | 5.029 | 0.728 | 0.508 | 0.868 |

### June 2019 (Recent Sample)
| Variable | Min | Max | Mean | Median | Std Dev |
|----------|-----|-----|------|--------|---------|
| swvl1 | 0.000 | 0.754 | 0.168 | 0.138 | 0.165 |
| swvl2 | 0.000 | 0.757 | 0.177 | 0.165 | 0.166 |
| slhf | -11.9M | 1.58M | -2.29M | -2.52M | 3.20M |
| sshf | -9.56M | 5.30M | -2.08M | -1.59M | 2.78M |
| lai_hv | 0.000 | 6.058 | 0.725 | 0.000 | 1.313 |
| lai_lv | 0.000 | 3.991 | 0.728 | 0.531 | 0.836 |

---

## 🎯 Next Steps

### 1. Data Preprocessing ✓ READY
Now that all data is downloaded, proceed with:

```bash
cd /burg-archive/home/mck2199/ML-Project
sbatch scripts/process_era5_land.sbatch
```

This will:
- Read GeoTIFF files with `rasterio`
- Regrid from 322×321 @ 0.1° → 256×256 @ 0.12°
- Crop to IndiaWeatherBench bounds
- Convert heat fluxes from accumulated J/m² to average W/m²
- Replicate monthly means to 6-hourly timesteps
- Convert to HDF5 and integrate with existing files

### 2. Compute Normalization Parameters
After preprocessing, update statistics:

```bash
sbatch scripts/compute_norm_params_era5land.sbatch
```

### 3. Validate Integration
Check integrated data:

```bash
python scripts/validate_era5land_integration.py
```

### 4. Train Expanded Model
Use new config with 43 variables:

```bash
sbatch scripts/train_unet_era5land.sbatch
```

---

## 📁 Files and Documentation

### Data Files
- **Location**: `/burg-archive/home/mck2199/ML-Project/data/era5_land_raw/`
- **Count**: 240 GeoTIFF files
- **Pattern**: `era5_land_YYYY_MM.tif`
- **Total Size**: 427 MB

### Documentation
- **This Report**: `ERA5_LAND_DOWNLOAD_COMPLETE.md`
- **Initial Sanity Check**: `ERA5_LAND_SANITY_CHECK.md`
- **Integration Guide**: `ERA5LAND_INTEGRATION.md`
- **GEE Setup**: `GEE_SETUP.md`
- **Visualization**: `data/era5_land_raw/sample_visualization.png`

---

## ✅ Final Validation Checklist

- [x] All 240 months downloaded (2000-2019)
- [x] All training months present (2000-2016: 204 months)
- [x] All validation months present (2017-2018: 24 months)
- [x] All test months present (2019: 12 months)
- [x] All files have 6 bands (variables)
- [x] All files have correct dimensions (322×321)
- [x] All files have correct CRS (EPSG:4326)
- [x] No NaN or Inf values in any file
- [x] 100% valid data coverage
- [x] Consistent file sizes (1.68-1.82 MB)
- [x] Spatial coverage includes IndiaWeatherBench region
- [x] Variable ranges are physically reasonable

---

## 🎉 Conclusion

**The ERA5-Land dataset download is COMPLETE and VALIDATED!**

All 240 months of data have been successfully downloaded from Google Earth Engine. The data quality is excellent with:
- ✓ Complete temporal coverage (training, validation, and test periods)
- ✓ All 6 required variables present
- ✓ No missing or invalid data
- ✓ Consistent structure across all files
- ✓ Proper spatial coverage of India region

**The dataset is ready for preprocessing and integration with IndiaWeatherBench!**

---

**Last Updated**: November 29, 2025  
**Validated By**: Automated sanity check scripts  
**Status**: ✅ READY FOR PREPROCESSING

