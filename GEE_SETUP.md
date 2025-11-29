# Google Earth Engine Setup for ERA5-Land Download

## Why Use Google Earth Engine Instead of Copernicus CDS?

✅ **Advantages**:
- More reliable API with better uptime
- No "cost limits exceeded" errors
- Faster data access
- Server-side processing capabilities
- Better for large-scale data extraction

## Setup Steps

### Step 1: Install Earth Engine API

Already done! The Earth Engine API has been installed in your venv:

```bash
# Already installed via:
# uv pip install earthengine-api
```

### Step 2: Authenticate with Google Earth Engine

You need to authenticate once:

```bash
cd /burg-archive/home/mck2199/ML-Project
source venv/bin/activate
earthengine authenticate
```

This will:
1. Open a browser window
2. Ask you to sign in with your Google account
3. Give you an authorization code
4. You paste the code back into the terminal

**Important**: Use your personal/institutional Google account. Earth Engine is free for research and education.

### Step 3: Verify Authentication

```bash
python -c "import ee; ee.Initialize(); print('✓ Authenticated successfully')"
```

If this works, you're ready to download data!

## ERA5-Land in Google Earth Engine

**Dataset**: `ECMWF/ERA5_LAND/HOURLY`

**Available Variables** (mapped to our names):
- `volumetric_soil_water_layer_1` → swvl1
- `volumetric_soil_water_layer_2` → swvl2
- `surface_latent_heat_flux` → slhf
- `surface_sensible_heat_flux` → sshf
- `leaf_area_index_high_vegetation` → lai_hv
- `leaf_area_index_low_vegetation` → lai_lv

**Coverage**:
- Spatial: Global (including India)
- Temporal: 1950 to near real-time
- Resolution: ~0.1° (11 km)
- Frequency: Hourly

## Download Methods

### Method 1: Batch Export to Google Drive (Recommended for Large Data)

**Pros**: Can handle any data volume
**Cons**: Requires manual file management

```bash
python scripts/download_era5_land_gee.py --use-drive
```

Then:
1. Monitor tasks at https://code.earthengine.google.com/tasks
2. Download files from Google Drive folder `era5_land_india`
3. Move files to `data/era5_land_raw/`

### Method 2: Direct Download with geemap (Best Option)

Install geemap for easier downloading:

```bash
uv pip install geemap
```

Then use the updated script (coming next).

### Method 3: Alternative - Use `geedim` Library

Another option for direct downloads:

```bash
uv pip install geedim
```

This library specializes in downloading large Earth Engine datasets.

## Recommended Approach

Given the size of your data request (20 years, 6 variables, hourly), I recommend:

**Option A - Month by Month with geemap**:
- Install `geemap`
- Use automated script to download each month
- Converts to GeoTIFF automatically
- Can monitor progress

**Option B - Use Pre-processed ERA5-Land from Another Source**:
- Some research institutions provide ERA5-Land subsets
- Check if your institution has a local copy
- Might be faster than downloading

## Quotas and Limits

Google Earth Engine quotas for free accounts:
- **Batch export**: Unlimited (but may queue)
- **Compute time**: Generous for research
- **Storage**: 250 GB in Drive (free tier)

**For your download**:
- 240 months × ~500 MB = ~120 GB total
- Should fit within free tier
- Batch exports queue automatically

## Troubleshooting

### "Earth Engine Not Authenticated"
```bash
earthengine authenticate --force
```

### "User Memory Limit Exceeded"
- Break into smaller time chunks
- Process fewer variables at once
- Use smaller spatial regions

### "Export Failed"
- Check task status at GEE Tasks page
- May need to reduce spatial resolution
- Try exporting to GeoTIFF instead of NetCDF

## Next Steps

1. **Authenticate**: Run `earthengine authenticate`
2. **Choose method**: Decide between Drive export vs direct download
3. **Run script**: Execute the appropriate download script
4. **Monitor**: Watch progress and download files

Would you like me to create an improved script using `geemap` for direct downloads?

