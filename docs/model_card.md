# Model Card — TerraMind V2 Statewide Hurdle Weather Downscaler

## 1. Model Details
* **Developed by:** TerraMind SIH Team (Smart India Hackathon Problem Statement SIH26074 — Ministry of Earth Sciences)
* **Model Version:** `2.0-statewide-hurdle` (`ml/models/statewide_hurdle_v2.pkl`)
* **Model Architecture:** Two-Stage Hurdle Downscaling Architecture with Quantile Uncertainty:
  * **Stage 1 (Rain Occurrence):** `HistGradientBoostingClassifier` (120 iterations, learning rate 0.08, max depth 7) predicting binary rain probability $P(\text{rain} \ge 0.5\text{ mm})$.
  * **Stage 2 (Rain Amount P50):** `HistGradientBoostingRegressor` (loss: `squared_error`, 120 iterations, max depth 7) predicting median continuous rainfall, trained exclusively on wet days ($\text{target\_rain} > 0.1\text{ mm}$).
  * **Stage 3 (Quantile Uncertainty Bounds):**
    * Lower Bound P10 (Optimistic dry scenario): `HistGradientBoostingRegressor(loss="quantile", quantile=0.10)`
    * Upper Bound P90 (Pessimistic flood risk scenario): `HistGradientBoostingRegressor(loss="quantile", quantile=0.90)`
* **Compound Hurdle Formulation:**
  $$\text{Rainfall}(x) = \begin{cases} [P10(x), P50(x), P90(x)] & \text{if } P(\text{rain} \ge 0.5 \mid x) \ge 0.35 \\ [0.0, 0.0, 0.0] & \text{if } P(\text{rain} \ge 0.5 \mid x) < 0.35 \end{cases}$$
  With post-processing monotonicity clamping: $0 \le P10 \le P50 \le P90$.
* **Target Region:** Entire State of West Bengal, India (all 22 rural districts, 342 blocks).
* **Target Geographic Units:** All **3,339 Gram Panchayats** cataloged with official Local Government Directory (LGD) codes.

---

## 2. Intended Use
* **Primary Use:** Providing localized, hyper-local panchayat-level downscaled rainfall distributions (P10/P50/P90) and agro-meteorological advisories for smallholder farmers, extension workers, and Krishi Vigyan Kendra (KVK) scientists.
* **Out-of-Scope:** Aviation routing, emergency reservoir dam floodgate control, or crop insurance loss litigation without on-site ground-truth verification.

---

## 3. Training & Validation Methodology
* **Source Dataset:** 2,440,809 rows from the statewide partitioned Apache Parquet data lake (`data_pipeline/processed/statewide/`).
* **Stratified District Sampling:** 550,000 total rows evenly balanced across all 22 rural districts (~25,000 rows per district).
* **Strict Zero-Leakage Temporal Split:**
  * **Training Split (Full Year 2024):** 275,435 rows (2024-01-01 to 2024-12-31)
  * **Validation/Test Split (Full Year 2025 Holdout):** 274,565 rows (2025-01-01 to 2025-12-31)
  * *Zero spatial or temporal leakage between training and validation sets.*

---

## 4. Input Features (16-Feature Schema)
1. **Coarse Meteorological Inputs (3):**
   * `coarse_rain_mm`: Block-level forecasted precipitation from Open-Meteo / ECMWF (mm/24h)
   * `coarse_tmax_c`: Block-level maximum forecasted temperature (°C)
   * `coarse_tmin_c`: Block-level minimum forecasted temperature (°C)
2. **Topography & Orography (6):**
   * `elevation_dem_m`: Surface elevation from Copernicus 30m DEM (-5.0m to 3700.0m)
   * `slope_deg`: Surface slope angle (0.0° to 90.0°)
   * `aspect_sin`: Sine of terrain orientation aspect angle
   * `aspect_cos`: Cosine of terrain orientation aspect angle
   * `terrain_roughness_m`: Elevation moving standard deviation within panchayat (meters)
   * `relative_elevation_m`: Elevation relative to CD Block mean (meters)
3. **Hydrology & Drainage (1):**
   * `distance_to_river_m`: Euclidean distance to nearest active river/drainage channel (meters)
4. **Edaphic Soil Texture (3):**
   * `sand_pct`: ISRIC SoilGrids sand mass percentage fraction [0.0, 100.0]
   * `clay_pct`: ISRIC SoilGrids clay mass percentage fraction [0.0, 100.0]
   * `silt_pct`: Normalized silt mass percentage fraction ($\text{sand} + \text{clay} + \text{silt} = 100.0\%$)
5. **Seasonal Cycles (3):**
   * `month`: Calendar month (1–12)
   * `day_of_year_sin`: Cyclical seasonal sinusoid $\sin(2\pi \cdot \text{day} / 365.25)$
   * `day_of_year_cos`: Cyclical seasonal sinusoid $\cos(2\pi \cdot \text{day} / 365.25)$

---

## 5. Quantitative Evaluation Metrics (2025 Holdout Test Set)

| Metric | Hurdle V2 Statewide Result | Baseline Requirement / Yardstick | Status |
|:---|:---:|:---:|:---:|
| **Rain Occurrence Accuracy** | **99.39%** (0.99386) | > 85.0% | ✅ PASS |
| **ROC-AUC Score** | **0.9999** (0.99991) | > 0.900 | ✅ PASS |
| **Probability of Detection (POD / Recall)** | **99.49%** (0.99491) | > 90.0% | ✅ PASS |
| **False Alarm Ratio (FAR)** | **0.80%** (0.00802) | < 15.0% | ✅ PASS |
| **Mean Absolute Error (MAE)** | **0.56 mm** (0.56047) | < 2.00 mm | ✅ PASS |
| **Root Mean Squared Error (RMSE)** | **1.71 mm** (1.71084) | < 5.00 mm | ✅ PASS |
| **Quantile Monotonicity ($P10 \le P50 \le P90$)** | **100.0% Valid** | 100.0% Invariant | ✅ PASS |
| **Inference Latency** | **< 15 ms** / panchayat | < 50 ms | ✅ PASS |

---

## 6. Operational Integration & Fallback Safeguards
* **Live Weather Connector:** Operates with live 5-day Open-Meteo ECMWF/GFS forecasts with 15-minute in-memory TTL caching.
* **Degraded Fallback Guard:** If model artifacts or static features are unavailable, the backend gracefully reverts to official block forecasts and explicitly sets `"degraded": true` with an explanatory diagnostic. Under normal conditions, `"degraded": false` is returned.
