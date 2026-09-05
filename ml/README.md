# TerraMind AI / ML & Data Engineering Guide

> **Assigned Owner:** Member 3 — AI / ML & Data Engineer  
> **Workspaces:** `ml/` and `data_pipeline/`  
> **Status:** Operational V1.3 XGBoost residual pipeline live. Degraded fallback active in production pending convective downscaling validation.

---

## 1. Welcome & Workspace Overview

You own the complete data-to-model pipeline for the TerraMind weather downscaling engine. Your objective is to downscale coarse block-level forecasts (~25 km) into accurate, hyper-local panchayat-level predictions (~2–5 km) across the 8 panchayats in Amdanga Block.

### Your Directory Layout
```text
ml/
├── pipelines/
│   └── train_pipeline_v1_3.py       # Main operational training pipeline
├── models/
│   ├── v1_3_rain_residual.pkl       # Active operational XGBoost residual model
│   ├── v1_3_rain_calibration.pkl    # Active baseline calibration model
│   ├── v1_3_metadata.pkl            # Model parameters, evaluation scores (POD = 0.92)
│   ├── v1_3_residual_feature_importance.csv  # Ranked feature importances
│   ├── v1_rain_classifier.pkl       # Rain occurrence classifier
│   └── v1_tmax_regressor.pkl        # Maximum temperature regressor
└── evaluations/
    ├── evaluate_rainfall_baselines.py         # M0 / M1 baseline RMSE measurement
    ├── evaluate_m3_spatial_downscaling.py     # Panchayat-to-panchayat spatial test
    └── test_v1_3_residual_strength.py         # Calibration vs residual validation

data_pipeline/
├── ingest/                          # Weather & satellite download scripts (Open-Meteo, IMERG, CHIRPS)
├── features/                        # Terrain & spatial feature extraction (SRTM DEM, slope, rivers)
├── metadata/                        # Static panchayat GPS coordinates & crop calendars
└── raw/                             # Cached datasets (CSVs, NetCDF, GeoJSONs — ignored in git)
```

---

## 2. What Changed Recently (Reorganization Summary)

The repository was refactored into modular, role-based workspaces so Frontend, Backend, ML, and DevOps can work simultaneously without merge conflicts:

1. **Dedicated Workspace:**
   * All ML pipelines moved into `ml/pipelines/`.
   * All evaluation scripts moved into `ml/evaluations/`.
   * All serialized models moved into `ml/models/`.
   * Ingestion and feature builders moved into `data_pipeline/ingest/` and `data_pipeline/features/`.
2. **Path Resolutions Updated:**
   * File references now resolve relative to project root (`data_pipeline/raw/`, `ml/models/`) with fallback handling, so scripts can be executed from anywhere.
3. **Repository Cleanliness & `.gitignore`:**
   * Operational V1.3 model artifacts (`v1_3_*.pkl`, `v1_*.pkl`) and feature importance CSVs are tracked and pushed to GitHub.
   * Large multi-gigabyte satellite NetCDF files (`.nc4`, `.tif`) and old experimental model dumps (`m3_clean_*`, `v1_2_*`) are git-ignored to keep clone times fast and adhere to SIH Handbook guidelines.
4. **Verified Clean Execution:**
   * The pipeline and all integration tests have been tested and pass with exit code 0.

---

## 3. Current Model Diagnostic (Where V1.3 Stands)

### ✅ What Is Working Well
* **Rain Event Detection (POD = 0.92):** The model catches **92%** of actual rainfall events. Farmers are almost never caught off-guard by unpredicted rain.
* **Temporal Discipline:** Training strictly respects time boundaries (Train: `< Sept 2024`, Val: `Sept–Dec 2024`, Test: `Jan 2025 onwards`). Zero target or time leakage.
* **Feature Pipeline:** 25 physics-derived and lagged features working reliably.

### ⚠️ Critical Limitations to Solve (The "Flat Delta" Challenge)
1. **Terrain Is Nearly Irrelevant in Amdanga (< 1% Feature Importance):**
   * *Diagnostic:* Elevation across Amdanga Block only varies between 5 m to 15 m. There is virtually no orographic lift to trigger localized rain shadows.
   * *Consequence:* Static DEM features (`elevation_dem_m`, `slope_deg`, `distance_to_river_m`) contribute almost zero explanatory power.
2. **Underestimation of Heavy Rainfall:**
   * *Diagnostic:* Heavy-rain RMSE (for rain $\ge$ 25 mm) is ~28.05 mm. Standard MSE / L2 loss penalizes large errors symmetrically, forcing the tree model to predict safe median values during severe monsoon storms.
3. **Short Training Horizon:**
   * *Diagnostic:* Current dataset spans only ~8 months of historical data (fewer than 30 heavy rain events).
4. **Current Operational Status (`degraded: true`):**
   * As advised by the SIH handbook, the production API currently falls back to coarse block forecasts with `"degraded": true` because spatial downscaling across adjacent flat villages did not reliably beat the baseline.

---

## 4. Your Action Plan & Next Steps (Priority ML Backlog)

### 🎯 Task 1: Implement Log-Transform & Tweedie Regression Loss (Fixes Heavy Rain Underestimation)
* **Problem:** MSE pulls extreme downpours toward the mean.
* **Solution:**
  1. Train the regressor on $\log(1 + \text{rain})$ and invert predictions with $\exp(x) - 1$.
  2. Switch XGBoost objective to **Tweedie regression**:
     ```python
     import xgboost as xgb

     reg = xgb.XGBRegressor(
         objective="reg:tweedie",
         tweedie_variance_power=1.5,  # 1.0 = Poisson, 2.0 = Gamma
         n_estimators=600,
         max_depth=6,
         learning_rate=0.03
     )
     ```
  3. Tweedie naturally models compound Poisson-Gamma processes (zero-inflated with a heavy positive tail).

---

### 🎯 Task 2: Ingest Dynamic Atmospheric Convective Physics (Replaces Flat Terrain)
* **Problem:** In flat Gangetic plains, storms (Nor'westers / Kalbaishakhi) are driven by atmospheric thermodynamics, not mountains.
* **Solution:** Add convective atmospheric variables from Open-Meteo / ERA5 into `data_pipeline/features/build_ml_dataset.py`:
  * **CAPE (Convective Available Potential Energy):** Measures atmospheric buoyancy and convective storm potential.
  * **Total Column Precipitable Water:** Total moisture content available in the vertical air column.
  * **850 hPa Wind Vectors ($U$ and $V$ components):** Tracks steering wind speed and cloud movement direction across the block.

---

### 🎯 Task 3: Expand Historical Horizon to 5–10 Years (2015–2024)
* **Problem:** 8 months of data lacks enough extreme monsoon depressions and cyclone events.
* **Solution:**
  * Update `data_pipeline/ingest/download_weather.py` and `download_imerg.py` to pull 10 full years of CHIRPS (0.05°) and ERA5 reanalysis.
  * This provides hundreds of extreme weather events across multiple monsoons.

---

### 🎯 Task 4: Implement 3-Stage Hurdle Architecture with Quantile Uncertainty (P10 / P50 / P90)
* **Concept (SIH Handbook Part 8.3):**
  A single number like "28 mm" is misleading. Providing confidence bounds (`P10` = 18 mm, `P50` = 28 mm, `P90` = 42 mm) is vastly better science and helps farmers make risk-weighted decisions.
* **Implementation:**
  Use LightGBM quantile regression:
  ```python
  import lightgbm as lgb

  quantile_models = {}
  for alpha in [0.1, 0.5, 0.9]:
      model = lgb.LGBMRegressor(
          objective="quantile",
          alpha=alpha,
          n_estimators=600,
          learning_rate=0.05
      )
      model.fit(X_train, y_train)
      quantile_models[alpha] = model
  ```
* Verify calibration: ~80% of test observations should fall between P10 and P90.

---

### 🎯 Task 5: Transition from "Degraded" Fallback to Validated Operational Downscaling
* Once the convective model proves superior spatial verification across the 8 panchayats, plug the new models into `backend/forecast_engine_v2.py`.
* Change `"degraded": false` in the API output. This achieves the core SIH problem statement!

---

## 5. How to Run & Test Locally

Activate your virtual environment and run the pipeline:

```bash
# 1. Run the operational V1.3 training pipeline
.venv/bin/python ml/pipelines/train_pipeline_v1_3.py

# 2. Run baseline evaluation
.venv/bin/python ml/evaluations/evaluate_rainfall_baselines.py

# 3. Run spatial verification
.venv/bin/python ml/evaluations/evaluate_m3_spatial_downscaling.py

# 4. Verify system integration tests
.venv/bin/python tests/test_forecast_advisories.py
```

---

## 6. Git Branch Workflow for ML

1. **Pull the latest code from `main`:**
   ```bash
   git checkout main
   git pull origin main
   ```
2. **Create your feature branch:**
   ```bash
   git checkout -b feature/ml-tweedie-experiments
   ```
3. **Keep git clean:**
   * Only commit code, small feature importance CSVs, and final validated `.pkl` weights in `ml/models/`.
   * Never force-add `.nc4`, `.tif`, or multi-gigabyte raw data files.
4. **Open a Pull Request:**
   * Push your branch to GitHub and ask the Manager/DevOps to review and merge into `main`.
