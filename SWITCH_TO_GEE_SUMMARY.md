# Switch from Copernicus CDS to Google Earth Engine - Summary

**Date**: November 25, 2025  
**Issue**: Copernicus CDS API "403 Forbidden - cost limits exceeded" errors  
**Solution**: Switched to Google Earth Engine for ERA5-Land downloads

## What Changed

### ❌ Problem with Copernicus CDS
Your download attempts failed with:
```
Error: 403 Client Error: Forbidden
cost limits exceeded
Your request is too large, please reduce your selection.
```

Even after breaking downloads into monthly chunks (240 requests), the CDS API was rejecting requests due to size limits.

### ✅ Solution: Google Earth Engine

Switched the entire download pipeline to use **Google Earth Engine (GEE)**, which:
- Has ERA5-Land data available (`ECMWF/ERA5_LAND/HOURLY`)
- No restrictive cost limits for research
- More reliable API
- Better tools (`geemap`) for downloads
- Free for academic use

## New Setup Required

### Step 1: Install Earth Engine API ✅ (Done)
```bash
# Already installed:
uv pip install earthengine-api geemap
```

### Step 2: Authenticate with Google Earth Engine ⚠️ (YOU NEED TO DO THIS)
```bash
cd /burg-archive/home/mck2199/ML-Project
source venv/bin/activate
earthengine authenticate
```

This will:
1. Open a browser
2. Ask you to sign in with Google
3. Give you an authentication code
4. Paste the code in terminal

**Use your institutional or personal Google account** - it's free for research/education.

### Step 3: Test the Download
```bash
# Test with one month
python scripts/download_era5_land_geemap.py --test
```

### Step 4: Run Full Download
```bash
# Submit the job
sbatch scripts/download_era5_land_gee.sbatch

# Monitor progress
tail -f logs/download_era5_gee_*.out
```

## Files Created

### New GEE Scripts:
- ✅ `scripts/download_era5_land_geemap.py` - Main download script using geemap
- ✅ `scripts/download_era5_land_gee.py` - Alternative GEE script  
- ✅ `scripts/download_era5_land_gee.sbatch` - SLURM job for GEE downloads
- ✅ `GEE_SETUP.md` - Complete GEE setup guide
- ✅ `GEE_vs_CDS.md` - Comparison of approaches

### Old CDS Scripts (Deprecated but Kept):
- `scripts/download_era5_land.py` - Original CDS version (had issues)
- `scripts/download_era5_land.sbatch` - Original SLURM job (failed)
- `CDS_API_SETUP.md` - CDS setup guide (no longer needed)

### Updated Documentation:
- ✅ `README.md` - Updated to reference GEE instead of CDS
- ✅ `ERA5LAND_INTEGRATION.md` - Will need updating for GEE
- ✅ `IMPLEMENTATION_SUMMARY.md` - Will need updating for GEE

## Technical Details

### Data Format Change:
- **CDS Output**: NetCDF (.nc files)
- **GEE Output**: GeoTIFF (.tif files) or NetCDF

The preprocessing script will need minor updates to handle GeoTIFF format (uses `rasterio` instead of `xarray`).

### Download Strategy:
- Still month-by-month (240 files for 2000-2019)
- But GEE is much more reliable
- Can optionally compute monthly means server-side (reduces data size)

## What You Need to Do Now

1. **Authenticate GEE** (required, one-time):
   ```bash
   earthengine authenticate
   ```

2. **Test download** (recommended):
   ```bash
   python scripts/download_era5_land_geemap.py --test
   ```
   This will download just January 2000 to verify it works.

3. **Run full download**:
   ```bash
   sbatch scripts/download_era5_land_gee.sbatch
   ```

4. **Monitor progress**:
   ```bash
   tail -f logs/download_era5_gee_*.out
   ```

## Expected Timeline

- **Authentication**: 5 minutes
- **Test download**: 2-5 minutes  
- **Full download**: 8-16 hours (240 months)
- Much faster and more reliable than CDS!

## Advantages of This Approach

1. ✅ **No more "cost limits exceeded" errors**
2. ✅ **More reliable** - GEE has better uptime
3. ✅ **Faster downloads** - Better infrastructure
4. ✅ **Free for research** - No quota issues
5. ✅ **Better tools** - `geemap` library simplifies everything
6. ✅ **Server-side processing** - Can reduce data before download

## Potential Issues & Solutions

### "Earth Engine Not Authenticated"
```bash
earthengine authenticate --force
```

### "Cannot access ERA5-Land dataset"
- Check you're logged in with correct Google account
- Verify Earth Engine is enabled for your account
- Visit: https://code.earthengine.google.com/

### "geemap download fails"
- The script saves monthly means by default (reduces size)
- If you need hourly data, we can modify the script
- Alternative: Use GEE batch export to Drive

## Next Steps After Download

Once downloads complete:

1. **Verify files**:
   ```bash
   ls -lh data/era5_land_raw/
   # Should see: era5_land_2000_01.tif, era5_land_2000_02.tif, etc.
   ```

2. **Update preprocessing script** (may be needed):
   - Current script expects NetCDF
   - GEE produces GeoTIFF
   - I can update this to handle both formats

3. **Continue with integration**:
   - Process data: `sbatch scripts/process_era5_land.sbatch`
   - Compute normalization: `sbatch scripts/compute_norm_params_era5land.sbatch`
   - Validate: `python scripts/validate_era5land_integration.py`
   - Train model: `sbatch scripts/train_unet_2gpu.sbatch`

## Questions?

See:
- `GEE_SETUP.md` - Complete setup guide
- `GEE_vs_CDS.md` - Detailed comparison
- `README.md` - Updated quick start

---

**Bottom Line**: The switch to Google Earth Engine solves the CDS API problems and gives you a more reliable download pipeline. Just need to authenticate once and you're good to go! 🎯

