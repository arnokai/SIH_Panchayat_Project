# TerraMind AI / ML & Data Engineering Guide & Roadmap

> **Assigned Owner:** Member 3 — AI / ML & Data Engineer  
> **Workspaces:** `ml/` and `data_pipeline/`  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Status:** Operational V1.3 XGBoost residual pipeline live. Degraded fallback active in production pending convective downscaling validation.

---

## 1. Executive Summary & Role Mission

As the **AI / ML & Data Engineer (Member 3)**, you own the mathematical and physical core of TerraMind:
1. **The Downscaling Pipeline:** Transforming coarse ~25 km atmospheric forecasts (ERA5 / IMDAA / Open-Meteo) into hyper-local ~2–5 km predictions tailored to each of the 8 Gram Panchayats in Amdanga Block.
2. **Atmospheric Physics Feature Engineering:** Fusing satellite gridded rainfall (CHIRPS / IMERG), soil moisture (SoilGrids), and convective atmospheric variables (CAPE, Precipitable Water, 850 hPa wind vectors).
3. **Probabilistic Quantile Uncertainty:** Outputting calibrated P10 / P50 / P90 confidence spreads so farmers receive honest probability distributions rather than a misleading single number.
4. **Lifting the "Degraded" Fallback:** Validating downscaling accuracy on an unseen test dataset so the production backend can switch from `degraded: true` to full operational machine learning (`degraded: false`).

---

## 2. Directory Layout & Key Files

```text
ml/
├── pipelines/
│   ├── train_pipeline_v1_3.py       # Operational baseline calibration + XGBoost residual pipeline
│   ├── train_pipeline_v1_4.py       # (In Development) Tweedie loss + convective atmospheric pipeline
│   └── train_quantile_models.py     # LightGBM P10, P50, P90 quantile regression models
├── models/
│   ├── v1_3_rain_residual.pkl       # Active operational residual model
│   ├── v1_3_rain_calibration.pkl    # Active baseline calibration model
│   ├── v1_3_metadata.pkl            # Evaluation metrics (POD = 0.92, MAE = 2.14 mm)
│   ├── v1_3_residual_feature_importance.csv  # Ranked feature contributions
│   ├── v1_rain_classifier.pkl       # Binary rain occurrence classifier
│   └── v1_tmax_regressor.pkl        # Maximum temperature regressor
└── evaluations/
    ├── evaluate_rainfall_baselines.py         # M0 / M1 baseline RMSE yardstick
    ├── evaluate_m3_spatial_downscaling.py     # Panchayat-to-panchayat spatial verification
    └── test_v1_3_residual_strength.py         # Calibration vs residual validation

data_pipeline/
├── ingest/                          # Weather & satellite download scripts (Open-Meteo, CHIRPS, ERA5)
├── features/                        # Feature extraction & dataset fusion (build_ml_dataset.py)
├── metadata/                        # Panchayat GPS boundaries, soil classifications, crop calendars
└── raw/                             # Cached training tables & historical weather (git-ignored)
```

---

## 3. Diagnostic of Current V1.3 Model (The "Flat Delta" Challenge)

### ✅ What Is Working Well
* **Rain Event Detection (POD = 0.92):** The binary model detects **92%** of real rain events.
* **Temporal Discipline:** Strictly time-split data (Train: `< Sep 2024`, Val: `Sep–Dec 2024`, Test: `Jan 2025+`). No target or future leakage.
* **Rapid Inference:** Prediction latency is `< 15 ms` per panchayat.

### ⚠️ Critical Gaps to Solve for SIH Jury Evaluation
1. **Terrain Is Nearly Irrelevant in Amdanga (< 1% Feature Importance):**
   * *Diagnostic:* Elevation across Amdanga Block only varies between 5 m to 15 m (delta plain). There is zero orographic lift to trigger localized rain shadows.
   * *Solution:* Ingest dynamic atmospheric convective variables (CAPE, Precipitable Water, wind vectors) to model localized storm cells (*Kalbaishakhi*).
2. **Underestimation of Heavy Rainfall Spikes:**
   * *Diagnostic:* Heavy-rain RMSE (for rain $\ge 25\text{ mm}$) is ~28.05 mm. Standard MSE loss penalizes large errors symmetrically, pulling predictions toward the safe median.
   * *Solution:* Log-transform target $\log(1 + \text{rain})$ and switch to **Tweedie regression loss**.
3. **Short Historical Horizon (8 Months):**
   * *Diagnostic:* Only ~8 months of data, with fewer than 30 heavy rain events.
   * *Solution:* Expand historical horizon to 10 years (2015–2024) using CHIRPS (0.05°) and ERA5.
4. **Current Operational Status (`degraded: true`):**
   * The backend currently returns `degraded: true` because spatial downscaling across flat adjacent villages did not reliably beat the baseline. Once the new convective model is validated, we promote it to `degraded: false`.

---

## 4. Action Plan & Task Checklist

### Phase 1: Heavy Rain Underestimation Fix (Tweedie Loss & Log-Transform)
- [ ] **1.1 Implement Log-Transform Pipeline:**
  - Train regressor on $\log(1 + \text{rain})$ to preserve high-magnitude spikes without exponential distortion. Invert predictions via $\exp(y) - 1$.
- [ ] **1.2 Switch to XGBoost Tweedie Objective:**
  - Implement Tweedie regression in `ml/pipelines/train_pipeline_v1_4.py`:
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
  - Naturally captures zero-inflated, right-skewed compound Poisson-Gamma rainfall distributions.

---

### Phase 2: Ingest Dynamic Atmospheric Convective Physics
- [ ] **2.1 Ingest Open-Meteo / ERA5 Upper-Air Variables:**
  - Add atmospheric instability parameters into `data_pipeline/ingest/download_weather.py`:
    - **CAPE (Convective Available Potential Energy):** Measures atmospheric buoyancy and thunderstorm trigger probability.
    - **Total Column Precipitable Water (TPW):** Measures absolute moisture content in the vertical column.
    - **850 hPa Wind Vectors ($ and $ components):** Captures monsoon drift direction and cloud speed across the 8 panchayats.
    - **Lifted Index / K-Index:** Classic thermodynamic storm severity indicators.
- [ ] **2.2 Re-run Feature Importance Analysis:**
  - Validate that CAPE and TPW replace elevation as top-3 predictive features in `ml/models/v1_4_residual_feature_importance.csv`.

---

### Phase 3: 10-Year Historical Data Expansion (2015–2024)
- [ ] **3.1 Batch Download Multi-Year Gridded Datasets:**
  - Download 10 years of CHIRPS (0.05° resolution) and ERA5-Land reanalysis for the Amdanga bounding box (`22.70°N–22.90°N, 88.40°E–88.65°E`).
- [ ] **3.2 Extreme Monsoon Event Inclusion:**
  - Ensure training captures major historical cyclone and monsoon depression events (Cyclone Amphan 2020, Cyclone Yaas 2021, Cyclone Remal 2024).

---

### Phase 4: 3-Stage Hurdle Architecture & Quantile Uncertainty (P10 / P50 / P90)
- [ ] **4.1 Build 3-Stage Model:**
  - **Stage 1 (Binary Classifier):** Will it rain? (`XGBClassifier`, threshold tuned for POD > 0.90).
  - **Stage 2 (Extreme Rain Trigger):** Rain $\ge 25\text{ mm}$ probability detector.
  - **Stage 3 (Quantile Regressor):** LightGBM quantile regression for P10 (optimistic), P50 (expected median), and P90 (pessimistic heavy downpour):
    ```python
    import lightgbm as lgb

    quantile_models = {}
    for alpha in [0.1, 0.5, 0.9]:
        m = lgb.LGBMRegressor(objective="quantile", alpha=alpha, n_estimators=600, learning_rate=0.05)
        m.fit(X_train, y_train)
        quantile_models[alpha] = m
    ```
- [ ] **4.2 Calibrate Empirical Coverage:**
  - Verify that ~80% of unseen test observations fall cleanly between the P10 and P90 bounds.

---

### Phase 5: Pest & Disease ML Classifiers
- [ ] **5.1 Paddy Blast (*Pyricularia oryzae*) Risk Model:**
  - Build classification model based on multi-day consecutive relative humidity $> 85\%$ and temperature window ($24^\circ\text{C} - 30^\circ\text{C}$).
- [ ] **5.2 Potato Late Blight (*Phytophthora infestans*) Warning Model:**
  - Train winter humidity/fog detector for high-risk blight periods.

---

### Phase 6: Production Model Packaging & Backend Promotion
- [ ] **6.1 Export Serialized Artifacts to `ml/models/`:**
  - Export `v1_4_rain_hurdle.pkl`, `v1_4_quantile_p10.pkl`, `v1_4_quantile_p50.pkl`, `v1_4_quantile_p90.pkl`, and `v1_4_metadata.pkl`.
- [ ] **6.2 Coordinate with Backend Engineer (Member 2):**
  - Integrate models into `backend/ml_service.py`.
  - Validate inference latency (`< 30 ms`).
  - Switch `degraded: false` in the production API.

---

## 5. Official Model Evaluation Table (For SIH Presentation Slide 3)

| Model Rung | Architecture / Features | Continuous RMSE | Continuous MAE | POD @ 2.5 mm | FAR @ 2.5 mm | CSI Skill Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M0 Baseline** | Coarse Block Value Copy | 8.42 mm | 4.12 mm | 0.81 | 0.32 | 0.59 |
| **M1 Physics** | Lapse-Rate + Bilinear Interpolation | 8.11 mm | 3.95 mm | 0.83 | 0.30 | 0.62 |
| **M2 Linear** | Linear Terrain Regression | 7.94 mm | 3.82 mm | 0.85 | 0.28 | 0.64 |
| **M3 GBT (V1.3)** | XGBoost Residual + Elevation/Soil | 6.84 mm | 2.14 mm | 0.92 | 0.21 | 0.74 |
| **M4 Target (V1.4)** | Tweedie Loss + Convective CAPE + Quantiles | **< 5.50 mm** | **< 1.80 mm** | **> 0.94** | **< 0.16** | **> 0.81** |

---

## 6. How to Run Training & Evaluations Locally

```bash
source .venv/bin/activate

# 1. Run operational training pipeline
python ml/pipelines/train_pipeline_v1_3.py

# 2. Run baseline evaluation yardstick
python ml/evaluations/evaluate_rainfall_baselines.py

# 3. Run spatial verification across the 8 panchayats
python ml/evaluations/evaluate_m3_spatial_downscaling.py

# 4. Verify system integration
python tests/test_forecast_advisories.py
```
