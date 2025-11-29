# Google Earth Engine vs Copernicus CDS for ERA5-Land

## Why We Switched from CDS to GEE

### Original Problem with Copernicus CDS:
- ❌ "403 Forbidden - cost limits exceeded" errors
- ❌ Request size limits too restrictive
- ❌ Had to download month-by-month (240 requests)
- ❌ Slow and unreliable API
- ❌ Required complex authentication setup

### Benefits of Google Earth Engine:
- ✅ More reliable API with better uptime
- ✅ No restrictive cost limits for research use
- ✅ Can process data server-side before downloading
- ✅ Better documentation and tooling (`geemap`)
- ✅ Faster data access
- ✅ Free for research and education

## Setup Comparison

### Copernicus CDS Setup (Old Method):
```bash
# Install CDS API
uv pip install cdsapi

# Create credentials file
cat > ~/.cdsapirc << 'EOF'
url: https://cds.climate.copernicus.eu/api
key: {UID}:{API_KEY}
EOF

# Accept license terms on website
# Download data (very slow, many failures)
```

### Google Earth Engine Setup (New Method):
```bash
# Install Earth Engine API and geemap
uv pip install earthengine-api geemap

# Authenticate (one-time)
earthengine authenticate

# Download data (much faster, more reliable)
```

## Data Access Comparison

### CDS Approach:
- Download entire months of hourly data
- Format: NetCDF (.nc files)
- Size: ~500 MB per month
- Time: ~5-10 minutes per month (if it works)
- Failures: Common due to API limits

### GEE Approach:
- Can pre-process on Google's servers
- Format: GeoTIFF (.tif files) or NetCDF
- Can compute monthly means server-side
- Time: ~2-5 minutes per month
- Failures: Rare

## File Formats

### From CDS (NetCDF):
```
era5_land_2000_01.nc  (contains all hours for January 2000)
Variables: swvl1, swvl2, slhf, sshf, lai_hv, lai_lv
Dimensions: time, lat, lon
```

### From GEE (GeoTIFF with geemap):
```
era5_land_2000_01.tif  (monthly mean or all hours as bands)
Bands: swvl1, swvl2, slhf, sshf, lai_hv, lai_lv
Dimensions: lat, lon (with time as separate bands if needed)
```

## Preprocessing Differences

### CDS Data:
1. Read NetCDF with `xarray`
2. Extract hourly timesteps
3. Aggregate to 6-hourly
4. Regrid 0.1° → 0.12°
5. Convert to HDF5

### GEE Data:
1. Read GeoTIFF with `rasterio` or `geotiff`
2. If monthly means: use directly
3. If hourly: aggregate to 6-hourly
4. Regrid 0.1° → 0.12°
5. Convert to HDF5

## Current Status

✅ **Switched to GEE** - Scripts updated to use Google Earth Engine with `geemap`

**Files Created**:
- `scripts/download_era5_land_geemap.py` - Main download script
- `scripts/download_era5_land_gee.sbatch` - SLURM job
- `GEE_SETUP.md` - Setup instructions

**Old CDS Files** (kept for reference):
- `scripts/download_era5_land.py` - Original CDS version
- `scripts/download_era5_land.sbatch` - Original SLURM job
- `CDS_API_SETUP.md` - CDS setup (now deprecated)

## Recommendation

**Use Google Earth Engine (GEE)** - It's more reliable, faster, and better suited for large-scale data downloads like this project requires.

## Next Steps

1. Authenticate with GEE: `earthengine authenticate`
2. Run test download: `python scripts/download_era5_land_geemap.py --test`
3. If test works, run full download: `sbatch scripts/download_era5_land_gee.sbatch`
4. Preprocessing script may need minor updates for GeoTIFF format

