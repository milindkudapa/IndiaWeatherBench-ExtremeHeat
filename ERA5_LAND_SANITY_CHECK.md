# ERA5-Land Data Sanity Check Report (Initial)

**Date**: November 29, 2025  
**Data Source**: Google Earth Engine  
**Status**: ⚠️ Partial Download (87.5% complete) - **SUPERSEDED**

> **⚠️ NOTE**: This was the initial sanity check. The download is now **100% complete**.  
> **See**: `ERA5_LAND_DOWNLOAD_COMPLETE.md` for the final validated report.

## Download Summary

### ✅ What We Have
- **Files Downloaded**: 210 out of 240 months (87.5%)
- **Total Size**: 374 MB (~1.8 MB per file)
- **Time Period Covered**: 2000-01 to 2017-06
- **Format**: GeoTIFF (.tif files)
- **Variables**: 6 bands per file (all expected variables)

### ✗ What's Missing
- **Missing Months**: 30 (12.5%)
- **Missing Period**: 2017-07 through 2019-12
- **Impact**: Missing validation set (2018) and test set (2019) entirely!

#### Missing Months Breakdown:
- 2017: July-December (6 months)
- 2018: All months (12 months) ← **Validation set**
- 2019: All months (12 months) ← **Test set**

## Data Quality Check

### ✅ File Structure (GOOD)
- **Dimensions**: 322 x 321 pixels
- **Bands**: 6 (correct)
- **CRS**: EPSG:4326 (WGS84)
- **Bounds**: [65.90°, 5.90°, 98.00°, 38.10°] ✓ (covers IndiaWeatherBench region)
- **Resolution**: ~0.1° per pixel ✓ (matches ERA5-Land native resolution)
- **Data Type**: float64 (will convert to float32 during processing)

### ✅ Variable Values (GOOD)

**Band Mapping** (verified from GEE):
- Band 1: `swvl1` → volumetric_soil_water_layer_1
- Band 2: `swvl2` → volumetric_soil_water_layer_2
- Band 3: `slhf` → surface_latent_heat_flux
- Band 4: `sshf` → surface_sensible_heat_flux
- Band 5: `lai_hv` → leaf_area_index_high_vegetation
- Band 6: `lai_lv` → leaf_area_index_low_vegetation

Sample statistics from January 2000:

| Band | Variable | Min | Max | Mean | Median | Std | Expected Range | Status |
|------|----------|-----|-----|------|--------|-----|----------------|--------|
| 1 | swvl1 | 0.000 | 0.677 | 0.127 | 0.112 | 0.133 | 0-0.6 m³/m³ | ✓ Good |
| 2 | swvl2 | 0.000 | 0.673 | 0.148 | 0.155 | 0.136 | 0-0.6 m³/m³ | ✓ Good |
| 3 | slhf | -9.4M | 424k | -830k | -224k | 1.2M | Accumulated J/m² | ⚠️ Need conversion |
| 4 | sshf | -7.0M | 732k | -1.3M | -798k | 1.5M | Accumulated J/m² | ⚠️ Need conversion |
| 5 | lai_hv | 0.000 | 6.482 | 0.775 | 0.000 | 1.381 | 0-10 m²/m² | ✓ Good |
| 6 | lai_lv | 0.000 | 5.029 | 0.728 | 0.508 | 0.868 | 0-10 m²/m² | ✓ Good |

### ⚠️ Heat Flux Values
The heat flux values (bands 3-4: slhf, sshf) show very large numbers (-9M to +732k). These are likely:
- **Accumulated fluxes** over the month (J/m²) rather than instantaneous rates (W/m²)
- **Will need conversion** during preprocessing to get proper W/m² values
- **Formula**: Divide by number of seconds in month to get average W/m²

### ✓ Data Completeness
- **No NaN values**: All pixels have valid data (100%)
- **Spatial coverage**: Complete coverage of India region
- **Temporal**: Monthly means (as expected from geemap download)

## Critical Issue: Missing Validation & Test Data

🚨 **PROBLEM**: The download stopped before completing 2018 and 2019!

- **2018** = Validation set (needed for model training)
- **2019** = Test set (needed for model evaluation)
- **Impact**: Cannot train or evaluate the expanded model without these!

### Why Did Download Stop?

Looking at the logs, `geemap.ee_export_image()` is failing for later months with:
```
Error: Expecting value: line 1 column 1 (char 0)
```

This suggests:
1. API timeout or rate limiting after ~210 requests
2. Possible quota/memory issues with GEE
3. Need to use batch export to Drive instead

## Solutions for Missing Data

### Option 1: Download Missing Months via Google Drive Export (Recommended)

Use the batch export method which is more reliable:

```bash
cd /burg-archive/home/mck2199/ML-Project
source venv/bin/activate
python scripts/download_missing_months.py
```

This will:
- Queue 30 export tasks to your Google Drive
- You monitor at https://code.earthengine.google.com/tasks
- Download completed files from Drive folder `era5_land_india`
- Move them to `data/era5_land_raw/`

### Option 2: Retry with Delays

Run the download script again with just the missing years:

```bash
python scripts/download_era5_land_geemap.py \
    --start-year 2017 \
    --end-year 2019
```

Add delays between requests to avoid rate limiting.

### Option 3: Use Alternative Data Source

If GEE continues to have issues:
- Download from Copernicus CDS (month-by-month might work)
- Use institutional data archive if available
- Download manually from GEE Code Editor

## Next Steps

### Immediate Action Required:

1. **Download missing 30 months** (2017-07 through 2019-12)
   - Use `scripts/download_missing_months.py` for batch export
   - OR retry with delays

2. **Verify complete coverage**:
   ```bash
   ls data/era5_land_raw/era5_land_*.tif | wc -l
   # Should be 240
   ```

3. **Once complete**, proceed with preprocessing

## Data Inspection Details

### File Format (GeoTIFF)
```
Filename: era5_land_2000_01.tif
Size: 1.8 MB
Bands: 6
Dimensions: 322 x 321 pixels
Resolution: 0.1°
Coordinate System: EPSG:4326 (WGS84)
```

### Spatial Coverage
- **Downloaded bounds**: 65.90° to 98.00°E, 5.90° to 38.10°N
- **Target bounds**: 66.60° to 97.25°E, 6.00° to 36.72°N
- **Status**: ✓ Good - downloaded area fully covers target region with buffer

### Preprocessing Requirements

When we process these GeoTIFF files:
1. **Read with `rasterio`** instead of `xarray`
2. **Regrid** from 322x321 @ 0.1° → 256x256 @ 0.12°
3. **Crop** to exact IndiaWeatherBench bounds
4. **Convert heat fluxes** from accumulated to rates (if needed)
5. **Convert to HDF5** and integrate with existing files

## Summary

### ✅ Good News:
- 87.5% of data successfully downloaded
- All 6 variables present in each file
- Data quality looks good (no NaN, reasonable ranges)
- Covers entire training period (2000-2016 complete)

### ⚠️ Issues to Resolve:
- Missing all of 2018 (validation set)
- Missing all of 2019 (test set)
- Missing last 6 months of 2017
- Heat flux values need conversion during preprocessing

### 🎯 Priority Action:
**Download the missing 30 months** - especially 2018 and 2019, as these are critical for model validation and testing.

---

**Next Command**:
```bash
python scripts/download_missing_months.py
```

This will queue batch exports to Google Drive for the missing months.

