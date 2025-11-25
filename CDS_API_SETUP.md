# Copernicus Climate Data Store (CDS) API Setup

## Prerequisites

Before downloading ERA5-Land data, you need to set up access to the Copernicus Climate Data Store (CDS).

## Step 1: Register for CDS Account

1. Go to: https://cds.climate.copernicus.eu/
2. Click "Register" and create a free account
3. Verify your email address

## Step 2: Get Your API Credentials

1. Log in to your CDS account
2. Go to your profile page: https://cds.climate.copernicus.eu/user
3. Scroll down to the "API key" section
4. You will see your:
   - UID (User ID)
   - API Key (a long string)

## Step 3: Configure CDS API on the Server

Create a file `~/.cdsapirc` with your credentials:

```bash
cat > ~/.cdsapirc << 'EOF'
url: https://cds.climate.copernicus.eu/api
key: {UID}:{API_KEY}
EOF
```

Replace `{UID}` with your User ID and `{API_KEY}` with your API key.

Example:
```bash
cat > ~/.cdsapirc << 'EOF'
url: https://cds.climate.copernicus.eu/api
key: 12345:abcd-efgh-1234-5678-ijklmnopqrst
EOF
```

Set appropriate permissions:
```bash
chmod 600 ~/.cdsapirc
```

## Step 4: Accept Terms and Conditions

**IMPORTANT**: Before you can download ERA5-Land data, you must accept the license terms:

1. Visit: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
2. Scroll down to the "Download data" tab
3. Review and accept the license terms
4. You only need to do this once

## Step 5: Verify Installation

Test that the CDS API is working:

```bash
cd /burg-archive/home/mck2199/ML-Project
source venv/bin/activate
python -c "import cdsapi; c = cdsapi.Client(); print('CDS API configured successfully!')"
```

If you see "CDS API configured successfully!", you're ready to download data!

## Downloading ERA5-Land Data

Once setup is complete, you can start the download:

```bash
# Submit the download job
sbatch scripts/download_era5_land.sbatch

# Monitor progress
tail -f logs/download_era5land_*.out
```

## Notes

- The download will take several hours (possibly 6-12 hours for 20 years of data)
- Downloads are done year by year to handle interruptions gracefully
- If a download fails, you can rerun the script and it will skip already downloaded years
- Each year's data will be ~2-5 GB in NetCDF format

## Troubleshooting

### "Invalid API key" error
- Double-check your UID and API key in `~/.cdsapirc`
- Make sure there are no extra spaces or line breaks

### "Terms and conditions not accepted" error
- Visit the ERA5-Land dataset page and accept the license terms

### Connection timeout
- CDS servers can be slow during peak times
- Try downloading during off-peak hours (evenings/weekends)

## References

- CDS API Documentation: https://cds.climate.copernicus.eu/how-to-api
- ERA5-Land Dataset: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
- Python cdsapi Package: https://github.com/ecmwf/cdsapi


