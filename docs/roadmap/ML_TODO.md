# TerraMind AI / ML & Data Engineering Guide & Roadmap

> **Assigned Owner:** Member 3 — AI / ML & Data Engineer  
> **Workspaces:** `ml/` and `data_pipeline/`  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Status:** Operational V2.0 Statewide Hurdle Model (`statewide_hurdle_v2.pkl`) live in production across 3,339 Gram Panchayats. Degraded fallback lifted (`degraded: false`).

---

## 1. Executive Summary & Role Mission

As the **AI / ML & Data Engineer (Member 3)**, you own the mathematical and physical core of TerraMind:
1. **The Statewide Downscaling Pipeline:** Transforming coarse ~25 km atmospheric forecasts (ECMWF / GFS / Open-Meteo) into hyper-local predictions tailored to all **3,339 Gram Panchayats** across all 22 rural districts of West Bengal.
2. **Atmospheric & Geospatial Feature Fusion:** Fusing static 14-column physical features (Copernicus DEM orography, SoilGrids edaphic texture, drainage network distances) with seasonal sinusoids and real-time atmospheric forcings.
3. **Probabilistic Quantile Uncertainty:** Outputting calibrated P10 / P50 / P90 confidence spreads so farmers receive actionable uncertainty bounds with guaranteed physical monotonicity ($0 \le P10 \le P50 \le P90$).
4. **Lifting the "Degraded" Fallback:** Successfully completed with `statewide_hurdle_v2.pkl` achieving 99.39% accuracy and 0.56 mm MAE on the untouched 2025 test horizon.

---

## 2. Directory Layout & Key Files

```text
ml/
├── pipelines/
│   ├── train_statewide_hurdle_model.py  # ACTIVE: Statewide 550k-row Two-Stage Hurdle + Quantile pipeline
│   └── train_pipeline_v1_3.py          # HISTORICAL: Pilot baseline calibration + XGBoost residual pipeline
├── models/
│   ├── statewide_hurdle_v2.pkl          # ACTIVE OPERATIONAL: Serialized 2.0 Hurdle + Quantiles artifact (1.54 MB)
│   ├── v1_3_rain_residual.pkl          # HISTORICAL: Pilot operational residual model
│   ├── v1_3_rain_calibration.pkl       # HISTORICAL: Pilot baseline calibration model
│   ├── v1_3_metadata.pkl               # HISTORICAL: Pilot evaluation metrics (POD = 0.92, MAE = 2.14 mm)
│   └── v1_3_residual_feature_importance.parquet  # Feature importances (Parquet)
└── evaluations/
    ├── compare_chirps_spatial.py
    ├── evaluate_m3_spatial_downscaling.py
    └── evaluate_rainfall_baselines.py

data_pipeline/
├── make_statewide_dataset.py            # ACTIVE: Master statewide 2.44M-row dataset generator
├── features/
│   ├── statewide_geo_features.py       # ACTIVE: 14-column static physical feature extraction engine
│   └── statewide_static_features.parquet # ACTIVE: 3,339 GPs static feature dataset
├── metadata/
│   ├── build_statewide_registry.py     # ACTIVE: Statewide LGD GP catalog builder
│   └── statewide_panchayats.parquet    # ACTIVE: 3,339 GP registry
└── processed/statewide/                 # ACTIVE: Pure Parquet lake partitioned by district_name=*
```

---

## 3. Diagnostic of Evolution: Overcoming the Pilot "Flat Delta" Challenge

The early Amdanga pilot (8 Gram Panchayats) revealed key scientific challenges:
1. **The "Flat Delta" Limitation:** Across 8 adjacent villages in North 24 Parganas, elevation varied by only 10 meters, offering minimal physical terrain forcing.
   * *Resolution:* Expanded the data lake statewide to all **3,339 Gram Panchayats across 22 rural districts**, capturing true orographic gradients (Darjeeling Himalayas, Western Rarh plateau, coastal delta).
2. **Zero-Inflation & Rainfall Underestimation:** Standard regression penalized extreme events symmetrically, pulling predictions toward zero.
   * *Resolution:* Implemented a **Two-Stage Hurdle Architecture** separating rain occurrence classification ($P(\text{rain} \ge 0.5\text{ mm}) \ge 0.35$) from positive-magnitude quantile regression.
3. **Deterministic vs. Probabilistic Uncertainty:** Single-number forecasts masked risk for farming decisions.
   * *Resolution:* Calibrated **multi-quantile bounds (P10, P50, P90)** using Scikit-Learn `HistGradientBoostingRegressor(loss="quantile")` with guaranteed physical monotonicity ($0 \le P10 \le P50 \le P90$).
4. **Static Forecast Fallbacks:**
   * *Resolution:* Built dynamic **Open-Meteo ECMWF/GFS weather integration** with 15-minute in-memory caching and offline Parquet fallback.

---

## 4. Action Plan & Task Checklist

### Phase 1: Heavy Rain Underestimation Fix & Two-Stage Separation
- [x] **1.1 Two-Stage Hurdle Separation:**
  - Implemented Stage 1 classification to handle zero-inflation followed by Stage 2 continuous regression on wet days ($\text{rain} > 0.1\text{ mm}$).
- [x] **1.2 Histogram Gradient Boosting Implementation:**
  - Deployed `HistGradientBoostingRegressor` with quantile loss functions replacing MSE/symmetric penalties.

---

### Phase 2: Weather Ingestion & Dynamic Atmospheric Connector
- [x] **2.1 Live Dynamic Weather Connector:**
  - Built `fetch_live_block_weather` in `backend/forecast_engine_v2.py` querying Open-Meteo ECMWF/GFS with 15-minute in-memory TTL caching.
- [x] **2.2 Offline Parquet Fallback:**
  - Graceful fallback to `data_pipeline/raw/coarse_block_forecast.parquet` on network timeout or offline flag.
- [ ] **2.3 Upper-Air Atmospheric Physics Expansion (Future Roadmap):**
  - Ingest convective indices (CAPE, Precipitable Water, 850 hPa wind vectors) for decadal reanalysis.

---

### Phase 3: Statewide Historical Data Expansion (2024–2025)
- [x] **3.1 3,339 Gram Panchayat Catalog:**
  - Built exhaustive verified catalog across 342 blocks and 22 rural districts (`statewide_panchayats.parquet`).
- [x] **3.2 2.44 Million Row Partitioned Lake:**
  - Generated full 2-year daily record (731 continuous days, 2024-01-01 to 2025-12-31) partitioned by `district_name=*` in pure Parquet format.
- [x] **3.3 14-Column Static Physical Feature Contract:**
  - Extracted DEM elevation, slope, aspect, roughness, relative elevation, river distance, and normalized soil texture (`sand + clay + silt == 100.0%`).

---

### Phase 4: Two-Stage Hurdle Architecture & Quantile Uncertainty (P10 / P50 / P90)
- [x] **4.1 Two-Stage Hurdle Pipeline (`train_statewide_hurdle_model.py`):**
  - Stage 1: `HistGradientBoostingClassifier` predicting rain occurrence (Accuracy: 99.39%, ROC-AUC: 0.9999).
  - Stage 2: `HistGradientBoostingRegressor` predicting P50 median rain amount (MAE: 0.56 mm).
  - Stage 3: Quantile regressors predicting P10 (optimistic) and P90 (flood risk) bounds.
- [x] **4.2 100% Quantile Monotonicity Verification:**
  - Verified $(0 \le P10 \le P50 \le P90)$ holds for 100.0% of predictions across the 2025 test horizon and unit test suite.

---

### Phase 5: Pest & Disease ML Classifiers (Active Priority / Roadmap)
- [x] **5.1 Deterministic Rule-Based Baseline:**
  - Handled via `rules/rules.yaml` (`blast_disease_risk`, `sandy_soil_dry_spell`, `heat_stress`).
- [ ] **5.2 Machine Learning Classifier for Paddy Blast (*Pyricularia oryzae*):**
  - Train ML classifier on multi-day consecutive relative humidity $> 85\%$ and temperature window ($24^\circ\text{C} - 30^\circ\text{C}$).
- [ ] **5.3 Potato Late Blight (*Phytophthora infestans*) Early Warning:**
  - Train winter humidity/fog detector for high-risk blight periods in Hooghly and Burdwan.

---

### Phase 6: Production Packaging & Backend Promotion
- [x] **6.1 Export Serialized Artifact:**
  - Serialized `ml/models/statewide_hurdle_v2.pkl` with sub-models, 16 features, and evaluation metrics.
- [x] **6.2 Backend Integration:**
  - Integrated into `backend/forecast_engine_v2.py` and `backend/api.py`.
- [x] **6.3 Promotion to Production (`degraded: false`):**
  - Lifted degraded mode. Backend serves live ML predictions with sub-15ms latency.
- [x] **6.4 Test Suite Pass:**
  - All 157 unit tests passing cleanly (`.venv/bin/python -m unittest discover -s tests`).

---

## 5. Official Model Evolution Table

| Model Rung | Architecture / Scope | Continuous MAE | Continuous RMSE | Accuracy | ROC-AUC | POD @ 0.5mm | Operational Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **M0 Baseline** | Coarse Block Copy (Amdanga Pilot) | 4.12 mm | 8.42 mm | — | — | 0.81 | Historical Scaffold |
| **M1 Physics** | Lapse-Rate + Bilinear (Pilot) | 3.95 mm | 8.11 mm | — | — | 0.83 | Historical Benchmark |
| **M2 Linear** | Linear Terrain Regression (Pilot) | 3.82 mm | 7.94 mm | — | — | 0.85 | Historical Benchmark |
| **M3 GBT (V1.3)** | XGBoost Residual + Soil (Pilot) | 2.14 mm | 6.84 mm | — | — | 0.92 | Historical Fallback |
| **V2.0 Hurdle (Current)** | **Statewide Two-Stage Hurdle + Quantiles (3,339 GPs)** | **0.56 mm** | **1.71 mm** | **99.39%** | **0.9999** | **0.9949** | **PRODUCTION LIVE (`degraded: false`)** |

---

## 6. How to Run Training, Evaluations & Verification Locally

```bash
# 1. Run Statewide Two-Stage Hurdle training pipeline (samples 550k rows across 22 districts)
.venv/bin/python ml/pipelines/train_statewide_hurdle_model.py

# 2. Inspect serialized model artifact and verify metrics
.venv/bin/python -c '
import joblib
art = joblib.load("ml/models/statewide_hurdle_v2.pkl")
print("Model Version:", art["model_version"])
print("Metrics:", art["metrics"])
print("Features count:", len(art["features"]))
'

# 3. Verify static Parquet schema and invariants (3,339 GPs, 0 NaNs)
.venv/bin/python -c '
import pandas as pd
df = pd.read_parquet("data_pipeline/features/statewide_static_features.parquet")
print("Shape:", df.shape)
assert (df["sand_pct"] + df["clay_pct"] + df["silt_pct"]).round(2).eq(100.0).all()
print("All static invariants valid!")
'

# 4. Run authoritative test suite (all 157 unit tests)
.venv/bin/python -m unittest discover -s tests
```
