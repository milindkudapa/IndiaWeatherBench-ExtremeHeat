# IndiaWeatherBench Analysis Notebooks

This directory contains Jupyter notebooks for analyzing the IndiaWeatherBench dataset and evaluating the trained UNet weather forecasting model.

## Notebooks Overview

### 1. Data Exploration (`01_data_exploration.ipynb`)
**Purpose**: Comprehensive exploration of the IndiaWeatherBench dataset integrated with ERA5-Land variables.

**Contents**:
- Dataset overview and structure
- Variable categorization (IMDAA atmospheric, ERA5-Land surface)
- Spatial domain visualization (terrain, land mask)
- Sample atmospheric variables (temperature, pressure, precipitation, wind)
- ERA5-Land variables (soil moisture, heat fluxes, LAI)
- Temporal coverage and seasonal patterns

**Figures**: `figures/01_data_exploration/`
- `01_static_fields.png` - Terrain and land mask
- `02_imdaa_atmospheric.png` - Surface atmospheric variables
- `03_era5land_variables.png` - ERA5-Land surface variables
- `04_temporal_distribution.png` - Data temporal coverage
- `05_seasonal_patterns.png` - Seasonal temperature and precipitation

---

### 2. UNet Model Evaluation (`02_unet_model_evaluation.ipynb`)
**Purpose**: Evaluate the trained UNet model's performance on the 2019 test dataset.

**Contents**:
- Model loading and configuration
- Training metrics visualization (RMSE by lead time)
- Seasonal test sample selection
- **Multi-step forecasting** (6h, 12h, 24h using autoregressive approach)
- Prediction vs ground truth comparison
- Multi-variable analysis (temperature, pressure, wind, RH, geopotential height)
- Precipitation context (model limitation noted)
- Spatial error analysis

**Key Features**:
- Autoregressive forecasting showing error accumulation over time
- Comprehensive multi-variable comparison
- Quantitative metrics (RMSE, MAE, bias, correlation)

**Figures**: `figures/02_unet_evaluation/`
- `model_rmse_by_leadtime.png` - Training performance metrics
- `seasonal_test_samples.png` - Temperature patterns across seasons
- `multi_leadtime_temperature.png` - **6h, 12h, 24h forecast comparison**
- `multi_variable_comparison.png` - 5 variables × 3 panels
- `precipitation_context.png` - Precipitation (not predicted by model)
- `spatial_error_analysis.png` - Regional error patterns

---

### 3. Heat Wave Analysis (`03_heatwave_analysis_may2019.ipynb`)
**Purpose**: Detailed analysis of the May 25 - June 1, 2019 heat wave event.

**Contents**:
- Heat wave characterization (temporal evolution, spatial extent)
- Peak temperature identification and analysis
- Model predictions during extreme event
- **Multi-lead time forecasts** (6h, 12h, 24h) during peak heat wave
- Extreme temperature region analysis (>40°C)
- Detection metrics (Precision, Recall, F1-score)
- Performance comparison: normal vs extreme conditions

**Key Findings**:
- Model captures spatial patterns of heat wave
- Cold bias observed in extreme temperature regions
- Moderate F1-score for extreme heat detection
- Errors accumulate significantly beyond 12h

**Figures**: `figures/03_heatwave_analysis/`
- `01_heatwave_temporal_evolution.png` - Temperature time series and distribution
- `02_heatwave_spatial_extent.png` - Peak temperature map and extreme regions
- `03_peak_heatwave_comparison.png` - Prediction vs ground truth at peak
- `04_multi_leadtime_heatwave_predictions.png` - **6h, 12h, 24h forecasts**
- `05_extreme_heat_detection.png` - Detection performance (TP/FP/FN)

---

## Directory Structure

```
notebooks/
├── 01_data_exploration.ipynb
├── 02_unet_model_evaluation.ipynb
├── 03_heatwave_analysis_may2019.ipynb
├── README.md (this file)
└── figures/
    ├── 01_data_exploration/
    │   ├── 01_static_fields.png
    │   ├── 02_imdaa_atmospheric.png
    │   ├── 03_era5land_variables.png
    │   ├── 04_temporal_distribution.png
    │   └── 05_seasonal_patterns.png
    ├── 02_unet_evaluation/
    │   ├── model_rmse_by_leadtime.png
    │   ├── seasonal_test_samples.png
    │   ├── multi_leadtime_temperature.png
    │   ├── multi_variable_comparison.png
    │   ├── precipitation_context.png
    │   └── spatial_error_analysis.png
    └── 03_heatwave_analysis/
        ├── 01_heatwave_temporal_evolution.png
        ├── 02_heatwave_spatial_extent.png
        ├── 03_peak_heatwave_comparison.png
        ├── 04_multi_leadtime_heatwave_predictions.png
        └── 05_extreme_heat_detection.png
```

## Running the Notebooks

### Prerequisites
```bash
# Activate virtual environment
source /burg-archive/home/mck2199/ML-Project/venv/bin/activate

# Ensure all dependencies are installed
uv pip install jupyter matplotlib seaborn numpy pandas h5py torch
```

### Execution Order
1. **Data Exploration** (optional, for understanding the dataset)
   ```bash
   jupyter notebook 01_data_exploration.ipynb
   ```

2. **Model Evaluation** (general performance assessment)
   ```bash
   jupyter notebook 02_unet_model_evaluation.ipynb
   ```

3. **Heat Wave Analysis** (extreme event case study)
   ```bash
   jupyter notebook 03_heatwave_analysis_may2019.ipynb
   ```

## Key Technical Details

### Model Architecture
- **Network**: UNet with encoder-decoder structure
- **Input**: 2 previous timesteps (T-12h, T-6h)
- **Output**: Next timestep (T+6h)
- **Variables**: 37 atmospheric variables (surface + pressure levels)
- **Grid**: 256×256 (6°N-36.72°N, 66.6°E-97.25°E)
- **Parameters**: ~10M

### Forecasting Approach
- **Single-step**: Direct 6h forecast
- **Multi-step**: Autoregressive (prediction feeds back as input)
  - 6h: 1 step
  - 12h: 2 steps
  - 24h: 4 steps

### Performance Metrics
- **RMSE**: Root Mean Squared Error
- **MAE**: Mean Absolute Error
- **Bias**: Mean Error (systematic over/under prediction)
- **Correlation**: Spatial correlation coefficient
- **F1-Score**: Harmonic mean of precision and recall (for extreme events)

## Data Sources

- **IMDAA**: Indian Monsoon Data Assimilation and Analysis (1979-2019)
- **ERA5-Land**: ECMWF Reanalysis Land Surface Data
- **Format**: HDF5 (`.h5` files)
- **Temporal Resolution**: 6-hourly
- **Spatial Resolution**: ~12 km

## References

- **IndiaWeatherBench Paper**: [arXiv:2509.00653](https://arxiv.org/abs/2509.00653)
- **Model Checkpoint**: `/burg-archive/home/mck2199/ML-Project/archive_baseline_unet/checkpoints/last.ckpt`
- **Data**: `/burg-archive/home/mck2199/ML-Project/data/indibench_h5/`
- **Code**: `/burg-archive/home/mck2199/ML-Project/IndiaWeatherBench/`

## Future Work

1. Update figure paths in notebooks 01 and 02 to use organized subdirectories
2. Compare with persistence and climatology baselines
3. Analyze additional extreme events (monsoon onset, cyclones)
4. Test ERA5-Land integrated model
5. Regional performance analysis
6. Ensemble forecasting experiments

---

**Last Updated**: December 2024  
**Author**: ML Project Team  
**Contact**: mck2199@columbia.edu

