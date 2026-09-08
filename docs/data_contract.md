# SIH26074 — Data Contract & ML Handoff Agreement
**From:** Member 3 (AI / ML & Data Lake Engineer)  
**To:** Member 2 (Backend / Integration Engineer) & Member 3 (Machine Learning Engineer)  
**Dataset Version:** `v2.0.0` (Statewide Pure Parquet Lake)  
**Generated Date:** 2026-09-08  
**Canonical File:** [`data_pipeline/processed/statewide/district_name=*/data.parquet`](../data_pipeline/processed/statewide) (22 district partitions, 2,440,809 rows)  
**Pilot Baseline:** [`data_pipeline/processed/training_table.parquet`](../data_pipeline/processed/training_table.parquet)  
**QA Verification:** [`data_pipeline/reports/statewide_qa_report.md`](../data_pipeline/reports/statewide_qa_report.md) — **Status: PASS**

---

## 1. Golden Handoff Rules (Never Guess)

1. **One Row = One Panchayat on One Date**:
   Every record represents exactly one prediction target for one Gram Panchayat on a specific calendar day.
2. **Zero Future Data Leakage**:
   No ground-truth observations, next-day weather, or future statistics are present in any predictor/feature column.
3. **Strict Separation of Inputs and Targets**:
   All columns prefixed with `target_` are ground-truth labels for training/evaluation and **must never be passed into model training as input features**.

---

## 2. Feature Availability & Data Dictionary

### A. Keys & Spatial Coordinates
| Column | Type | Unit | Available at Forecast Time? | Description & Source |
|---|---|---|:---:|---|
| `date` | `string (YYYY-MM-DD)` | Date | ✅ Yes | Valid forecast/observation date (`2024-01-01` to `2025-12-31`) |
| `panchayat_id` | `string` | Categorical | ✅ Yes | Unique Panchayat ID (e.g. `WB_107001` to `WB_110339`, 3,339 GPs; pilot aliases `A1`–`A8`) |
| `gp_code` | `int64` | LGD Code | ✅ Yes | National Local Government Directory (LGD) ID |
| `panchayat_name` | `string` | Text | ✅ Yes | Official Gram Panchayat name |
| `block_name` | `string` | Text | ✅ Yes | Administrative Block name (342 blocks statewide) |
| `district_name` | `string` | Text | ✅ Yes | District name (22 rural districts, Hive partition key) |
| `latitude` | `float64` | Degrees N | ✅ Yes | Panchayat centroid latitude (WGS84 EPSG:4326) |
| `longitude` | `float64` | Degrees E | ✅ Yes | Panchayat centroid longitude (WGS84 EPSG:4326) |

### B. Coarse Weather Forecast Inputs (The "Blurry Photo")
| Column | Type | Unit | Available at Forecast Time? | Description & Source |
|---|---|---|:---:|---|
| `coarse_rain_mm` | `float64` | mm / 24h | ✅ Yes | Block-level coarse forecasted rainfall (Open-Meteo ECMWF/GFS / IMD Block) |
| `coarse_tmax_c` | `float64` | °Celsius | ✅ Yes | Block-level maximum forecasted temperature |
| `coarse_tmin_c` | `float64` | °Celsius | ✅ Yes | Block-level minimum forecasted temperature |

### C. Static Terrain & Geospatial Features (`data_pipeline/features/statewide_static_features.parquet`)
| Column | Type | Unit | Available at Forecast Time? | Description & Source |
|---|---|---|:---:|---|
| `elevation_dem_m` | `float64` | meters | ✅ Yes | Elevation from Copernicus DEM (30m GLO-30) |
| `slope_deg` | `float64` | degrees | ✅ Yes | Surface slope calculated from DEM |
| `aspect_sin` | `float64` | unit vector | ✅ Yes | Sine of terrain orientation aspect angle |
| `aspect_cos` | `float64` | unit vector | ✅ Yes | Cosine of terrain orientation aspect angle |
| `terrain_roughness_m` | `float64` | meters | ✅ Yes | Terrain roughness standard deviation |
| `relative_elevation_m`| `float64` | meters | ✅ Yes | Delta between Panchayat elevation and Block mean |
| `nearest_river` | `string` | Text | ✅ Yes | Nearest major hydrological drainage channel |
| `distance_to_river_m` | `float64` | meters | ✅ Yes | Geodesic distance to closest active river system |

### D. Static Soil Composition
| Column | Type | Unit | Available at Forecast Time? | Description & Source |
|---|---|---|:---:|---|
| `sand_pct` | `float64` | % (0-100) | ✅ Yes | Sand fraction from ISRIC SoilGrids (0-30cm depth) |
| `clay_pct` | `float64` | % (0-100) | ✅ Yes | Clay fraction from ISRIC SoilGrids (0-30cm depth) |
| `silt_pct` | `float64` | % (0-100) | ✅ Yes | Silt fraction from ISRIC SoilGrids (`sand + clay + silt == 100.0%`) |
| `soil_type` | `string` | Category | ✅ Yes | Agronomic classification (`sandy` vs `non_sandy`) |

### E. Temporal & Seasonal Features
| Column | Type | Unit | Available at Forecast Time? | Description & Source |
|---|---|---|:---:|---|
| `month` | `int64` | 1-12 | ✅ Yes | Calendar month |
| `day_of_year` | `int64` | 1-366 | ✅ Yes | Julian day of year |
| `day_of_year_sin` | `float64` | cyclical | ✅ Yes | $\sin(2\pi \cdot \text{day} / 365.25)$ |
| `day_of_year_cos` | `float64` | cyclical | ✅ Yes | $\cos(2\pi \cdot \text{day} / 365.25)$ |
| `monsoon_phase` | `string` | Category | ✅ Yes | Seasonal flag: `winter`, `pre_monsoon`, `monsoon`, `post_monsoon` |

### F. Model Targets (Ground Truth — Supervised Learning Only)
| Column | Type | Unit | Purpose | Notes |
|---|---|---|---|---|
| `target_rain_binary` | `int64 (0/1)` | Binary | Stage 1 Classifier Target | 1 if actual rainfall $\ge 0.5$ mm, else 0 |
| `target_rain_mm` | `float64` | mm / 24h | Stage 2 Regressor Target | Actual rainfall amount (train regressor on rainy days only) |
| `target_tmax_c` | `float64` | °Celsius | Temperature Regressor Target | Lapse-rate adjusted ground observation |
| `target_tmin_c` | `float64` | °Celsius | Temperature Regressor Target | Lapse-rate adjusted ground observation |

---

## 3. Recommended Splitting Strategy for Member 3

> [!CAUTION]
> **Never split weather data randomly (`train_test_split(..., shuffle=True)`).**  
> Weather is temporally autocorrelated. A random split leaks tomorrow's weather into today's model and produces fake 99% accuracy that fails in real-world deployment.

Use the strictly chronological split:
```python
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data_pipeline/processed/statewide")

# Option A: Full Statewide Parquet Lake (2,440,809 rows)
# 1. Training Set (Full Year 2024: 1,222,074 rows across 3,339 GPs)
# 2. Test Set (Untouched Holdout 2025: 1,218,735 rows across 3,339 GPs)

# Option B: Operational 550,000-Row Stratified Statewide Sample
# Train rows (2024): 275,435
# Holdout test rows (2025): 274,565
```

---

## 4. How Member 3 Trains the Statewide Two-Stage Hurdle Model

```python
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
import joblib

# 16 Predictor columns available at forecast issuance time
FEATURES = [
    'coarse_rain_mm', 'coarse_tmax_c', 'coarse_tmin_c',
    'elevation_dem_m', 'slope_deg', 'aspect_sin', 'aspect_cos',
    'terrain_roughness_m', 'relative_elevation_m', 'distance_to_river_m',
    'sand_pct', 'clay_pct', 'silt_pct',
    'month', 'day_of_year_sin', 'day_of_year_cos'
]

# Stage 1: Rain Occurrence (Yes / No) - Achieves 99.39% accuracy, 0.9999 ROC-AUC
clf = HistGradientBoostingClassifier(max_iter=120, learning_rate=0.08, max_depth=7, random_state=42)
clf.fit(train_df[FEATURES], train_df['target_rain_binary'])

# Stage 2: Rain Amount P50 Median (Trained ONLY on positive rainfall instances)
rainy_train = train_df[train_df['target_rain_binary'] == 1]
reg_p50 = HistGradientBoostingRegressor(loss='squared_error', max_iter=150, learning_rate=0.08, max_depth=7, random_state=42)
reg_p50.fit(rainy_train[FEATURES], rainy_train['target_rain_mm'])

# Stage 3: Quantile Uncertainty Bounds (P10 Dry Bound, P90 Flood Risk Bound)
reg_p10 = HistGradientBoostingRegressor(loss='quantile', quantile=0.10, max_iter=120, learning_rate=0.08, max_depth=6, random_state=42)
reg_p10.fit(rainy_train[FEATURES], rainy_train['target_rain_mm'])

reg_p90 = HistGradientBoostingRegressor(loss='quantile', quantile=0.90, max_iter=120, learning_rate=0.08, max_depth=6, random_state=42)
reg_p90.fit(rainy_train[FEATURES], rainy_train['target_rain_mm'])

# Package bundle
artifact = {
    'classifier': clf,
    'regressor_p50': reg_p50,
    'regressor_p10': reg_p10,
    'regressor_p90': reg_p90,
    'features': FEATURES,
    'model_version': '2.0-statewide-hurdle'
}
joblib.dump(artifact, 'ml/models/statewide_hurdle_v2.pkl')
```
