# SIH26074 — Data Contract & ML Handoff Agreement
**From:** Member 1 (Data Engineer / Pipeline Owner)  
**To:** Member 2 (Machine Learning Engineer)  
**Dataset Version:** `v1.0.0`  
**Generated Date:** 2026-09-08  
**Canonical File:** [`data_pipeline/processed/training_table.parquet`](file:///home/arnokai/Projects/SIH_Panchayat_Project/data_pipeline/processed/training_table.parquet)  
**Inspection File:** [`data_pipeline/processed/training_table.csv`](file:///home/arnokai/Projects/SIH_Panchayat_Project/data_pipeline/processed/training_table.csv)  
**QA Verification:** [`data_pipeline/reports/qa_report.md`](file:///home/arnokai/Projects/SIH_Panchayat_Project/data_pipeline/reports/qa_report.md) — **Status: PASS**

---

## 1. Golden Handoff Rules (Never Guess)

1. **One Row = One Panchayat on One Date**:
   Every record represents exactly one prediction target for one Gram Panchayat on a specific calendar day.
2. **Zero Future Data Leakage**:
   No ground-truth observations, next-day weather, or future statistics are present in any predictor/feature column.
3. **Strict Separation of Inputs and Targets**:
   All columns prefixed with `target_` or `observed_` are ground-truth labels for training/evaluation and **must never be passed into model training as input features**.

---

## 2. Feature Availability & Data Dictionary

### A. Keys & Spatial Coordinates
| Column | Type | Unit | Available at Forecast Time? | Description & Source |
|---|---|---|:---:|---|
| `date` | `string (YYYY-MM-DD)` | Date | ✅ Yes | Valid forecast/observation date |
| `panchayat_id` | `string (A1-A8)` | Categorical | ✅ Yes | Unique Panchayat code within Amdanga Block |
| `gp_code` | `int64` | LGD Code | ✅ Yes | National Local Government Directory (LGD) ID |
| `panchayat_name` | `string` | Text | ✅ Yes | Gram Panchayat name (e.g. ADHATA, AMDANGA) |
| `latitude` | `float64` | Degrees N | ✅ Yes | Panchayat centroid latitude (WGS84 EPSG:4326) |
| `longitude` | `float64` | Degrees E | ✅ Yes | Panchayat centroid longitude (WGS84 EPSG:4326) |

### B. Coarse Weather Forecast Inputs (The "Blurry Photo")
| Column | Type | Unit | Available at Forecast Time? | Description & Source |
|---|---|---|:---:|---|
| `coarse_rain_mm` | `float64` | mm / 24h | ✅ Yes | Block-level coarse forecasted rainfall (Open-Meteo / IMD Block) |
| `coarse_tmax_c` | `float64` | °Celsius | ✅ Yes | Block-level maximum forecasted temperature |
| `coarse_tmin_c` | `float64` | °Celsius | ✅ Yes | Block-level minimum forecasted temperature |

### C. Static Terrain & Geospatial Features
| Column | Type | Unit | Available at Forecast Time? | Description & Source |
|---|---|---|:---:|---|
| `elevation_dem_m` | `float64` | meters | ✅ Yes | Elevation from Copernicus DEM / SRTM (30m) |
| `slope_deg` | `float64` | degrees | ✅ Yes | Surface slope calculated from DEM |
| `aspect_sin` | `float64` | unit vector | ✅ Yes | Sine of terrain orientation aspect angle |
| `aspect_cos` | `float64` | unit vector | ✅ Yes | Cosine of terrain orientation aspect angle |
| `terrain_roughness_m` | `float64` | meters | ✅ Yes | Standard deviation of elevation within Panchayat |
| `relative_elevation_m`| `float64` | meters | ✅ Yes | Delta between Panchayat elevation and Block mean |
| `nearest_river` | `string` | Text | ✅ Yes | Major hydrological feature (e.g. Ganges) |
| `distance_to_river_m` | `float64` | meters | ✅ Yes | Euclidean distance to closest active river/drainage line |

### D. Static Soil Composition
| Column | Type | Unit | Available at Forecast Time? | Description & Source |
|---|---|---|:---:|---|
| `sand_pct` | `float64` | % (0-100) | ✅ Yes | Sand fraction from SoilGrids (0-30cm depth) |
| `clay_pct` | `float64` | % (0-100) | ✅ Yes | Clay fraction from SoilGrids (0-30cm depth) |
| `silt_pct` | `float64` | % (0-100) | ✅ Yes | Silt fraction from SoilGrids (normalized so sum = 100%) |
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
| `target_tmax_c` | `float64` | °Celsius | Temperature Regressor Target | Lapse-rate adjusted ground temperature |
| `target_tmin_c` | `float64` | °Celsius | Temperature Regressor Target | Lapse-rate adjusted ground temperature |
| `chirps_rain_mm` | `float64` | mm / 24h | Observation Source | High-resolution satellite observation (0.05°) |
| `imd_rain_mm` | `float64` | mm / 24h | Observation Source | Official IMD gridded daily rainfall |
| `qa_flag` | `string` | PASS/FAIL | Audit | Pipeline QA approval flag |

---

## 3. Recommended Splitting Strategy for Member 2

> [!CAUTION]
> **Never split weather data randomly (`train_test_split(..., shuffle=True)`).**  
> Weather is temporally autocorrelated. A random split leaks the tomorrow's weather into today's model and produces fake 99% accuracy that fails in real life.

Use the strictly chronological split:
```python
import pandas as pd

df = pd.read_parquet("data_pipeline/processed/training_table.parquet")

# 1. Training Set (Full Year 2024: 2,928 rows)
train_df = df[df['date'] < "2025-01-01"]

# 2. Validation Set (H1 2025: 1,448 rows)
val_df = df[(df['date'] >= "2025-01-01") & (df['date'] < "2025-07-01")]

# 3. Test Set (Untouched Holdout H2 2025: 1,472 rows)
test_df = df[df['date'] >= "2025-07-01"]
```

---

## 4. How Member 2 Trains the Two-Stage Hurdle Model

```python
from xgboost import XGBClassifier, XGBRegressor

# Predictor columns (all features available at forecast time)
FEATURES = [
    'coarse_rain_mm', 'coarse_tmax_c', 'coarse_tmin_c',
    'elevation_dem_m', 'slope_deg', 'aspect_sin', 'aspect_cos',
    'terrain_roughness_m', 'relative_elevation_m', 'distance_to_river_m',
    'sand_pct', 'clay_pct', 'silt_pct',
    'day_of_year_sin', 'day_of_year_cos'
]

# Stage 1: Rain Occurrence (Yes / No)
clf = XGBClassifier(n_estimators=100, max_depth=4, random_state=42)
clf.fit(train_df[FEATURES], train_df['target_rain_binary'])

# Stage 2: Rain Amount (Trained ONLY on days where it actually rained)
rainy_train = train_df[train_df['target_rain_binary'] == 1]
reg = XGBRegressor(n_estimators=150, max_depth=4, objective='reg:tweedie', random_state=42)
reg.fit(rainy_train[FEATURES], rainy_train['target_rain_mm'])

# Inference Combination: Final Rain = P(Rain) * Rain Amount
prob_rain = clf.predict_proba(test_df[FEATURES])[:, 1]
pred_amount = reg.predict(test_df[FEATURES])
final_panchayat_rain = prob_rain * pred_amount
```
