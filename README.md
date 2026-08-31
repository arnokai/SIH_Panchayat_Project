# TerraMind — Panchayat-Level Weather Intelligence & Agricultural Advisory

> **SIH project prototype for localized weather intelligence and agricultural decision support**

TerraMind is a prototype decision-support system designed to provide **panchayat-level weather information and agricultural advisories**. The system combines panchayat location, terrain characteristics, historical weather data, multiple gridded rainfall products, machine-learning models, and rule-based agricultural logic.

The project is currently in **research/prototype development**. The machine-learning work has progressed from an initial V1 baseline to a V1.3 rainfall-calibration architecture.

---

## 1. Project Overview

Instead of treating an entire region as having one identical weather condition, TerraMind is designed around the needs of an individual panchayat.

The overall system is:

```text
Panchayat
    ↓
Panchayat geography + terrain + weather information
    ↓
ML / Rainfall Forecasting Layer
    ↓
Rainfall + Rain Probability + Tmax
    ↓
Agricultural Advisory Engine
    ↓
Web Dashboard
```

The current application is intended to provide:

- 🌧️ Rainfall estimation
- ☔ Rain probability / rain-event information
- 🌡️ Maximum-temperature estimation
- 🌱 Rule-based agricultural advisories
- 🇮🇳 English + Bengali advisory text
- 📍 Panchayat-specific information

---

# 2. Current Project Status

```text
Project stage:       Prototype / Research Development
Current ML version:  V1.3
Stable Git branch:   main
Development branch:  v2-development
Frontend branch:     frontend-development
```

The repository is currently maintained as a **private GitHub repository for the development team**.

V1.3 is the current experimental ML checkpoint. The model is not a production weather service and should not be treated as a replacement for official meteorological or agricultural advisories.

---

# 3. What TerraMind Does

For a selected panchayat, TerraMind is designed to process:

```text
Panchayat identity
      +
Latitude / Longitude
      +
Elevation and terrain
      +
Historical weather
      +
Rainfall products
      ↓
Forecasting / estimation
      ↓
Agricultural advisory
```

The advisory layer converts forecast information into simple action-oriented guidance.

Example:

```text
Light rain. Safe to apply light fertilisers.

হালকা বৃষ্টি। সার প্রয়োগ করা নিরাপদ।
```

The advisory logic is configured through `rules.yaml`.

---

# 4. Current Machine-Learning Architecture

The project has been developed incrementally.

## V1 — Initial Forecasting Baseline

The first V1 system established the core ML forecasting pipeline using historical weather and panchayat-level features.

Initial architecture:

```text
Historical Weather
        +
Panchayat Features
        ↓
Rain Classifier
        +
Rainfall Regressor
        +
Tmax Regressor
        ↓
Forecast Output
```

The original V1 model artifacts are:

```text
models/v1_rain_classifier.pkl
models/v1_rain_regressor.pkl
models/v1_tmax_regressor.pkl
```

V1 served as the baseline for later experiments.

---

# 5. V1.1 — Terrain Feature Experiment

V1.1 investigated whether local physical geography could improve prediction.

DEM-derived features were introduced:

```text
elevation_dem_m
slope_deg
aspect_sin
aspect_cos
terrain_roughness_m
relative_elevation_m
```

These were combined with existing panchayat geography, weather history, rainfall lags, and seasonal features.

The purpose of V1.1 was to test whether local terrain information could add useful spatial information.

The experiment confirmed that terrain features could be incorporated into the pipeline, but they did not by themselves solve the rainfall downscaling problem.

Intermediate V1.1 artifacts are retained locally for experimentation rather than being treated as the current production/prototype checkpoint.

---

# 6. V1.2 — Higher-Resolution Rainfall Reference Experiment

V1.2 expanded the rainfall-data investigation.

Three rainfall sources were examined:

```text
IMD       → 0.25° gridded rainfall
IMERG     → 0.10° precipitation
CHIRPS v3 → 0.05° rainfall
```

## IMD

The IMD 0.25° product mapped the eight study panchayats to two effective grid cells.

## IMERG

The IMERG 0.10° subset produced three effective rainfall series in the study area.

## CHIRPS

CHIRPS v3 provided the finest spatial resolution tested in the project:

```text
0.05° ≈ 5 km
```

The extracted CHIRPS dataset contained:

```text
5,112 rows
8 Panchayats
639 days
2024-01-01 → 2025-09-30
```

The eight panchayat coordinates produced:

```text
7 unique daily rainfall series out of 8 Panchayats
```

This was substantially more spatial differentiation than the coarser rainfall products tested earlier.

---

# 7. V1.2 Target Design

The rainfall target was changed so that the model predicts the next day's CHIRPS rainfall:

```text
Information available on day T
              ↓
           ML model
              ↓
CHIRPS rainfall on day T+1
```

The V1.2 feature set included:

```text
Panchayat geography
DEM terrain features
Historical rainfall lags
Rolling rainfall totals
Historical temperature lags
IMERG rainfall
IMD rainfall
Seasonal features
```

The final dataset contained:

```text
5,048 rows
35 columns
8 Panchayats
```

The first observations were removed where sufficient lag history was unavailable.

---

# 8. V1.2 Results

The V1.2 rainfall model was evaluated with a temporal split.

```text
Training:
2024-01-08 → 2024-08-31

Validation:
2024-09-01 → 2024-12-31

Testing:
2025-01-01 → 2025-09-29
```

Final V1.2 rainfall test results:

```text
Baseline RMSE: 11.44 mm
Model RMSE:     9.72 mm
Improvement:   15.0%

Model MAE:      5.39 mm

POD:            0.52
FAR:            0.23
CSI:            0.45
```

Temperature results:

```text
Tmax RMSE: 1.58 °C
Tmax MAE:  1.20 °C
Tmax Bias: -0.12 °C
```

### V1.2 limitation

Detailed error analysis showed that the model could detect many rainfall events but significantly underestimated heavy rainfall.

For actual CHIRPS rainfall above 25 mm:

```text
Heavy-rain RMSE ≈ 35 mm
```

The largest errors were concentrated in the monsoon period, especially June and July.

This led to the next experiment.

---

# 9. V1.3 — Multi-Source Rainfall Calibration + Residual Correction

V1.3 changed the rainfall-amount strategy.

Instead of asking XGBoost to learn the entire rainfall amount from scratch, the system first creates a calibrated rainfall estimate from multiple rainfall products.

The calibration inputs are:

```text
IMERG rainfall
IMD rainfall
Open-Meteo rainfall
```

The architecture is:

```text
IMERG ──────┐
            │
IMD ────────┼──→ Linear Rainfall Calibration
            │
Open-Meteo ─┘
                    ↓
             Calibrated Rainfall
                    ↓
             Residual Correction
                    ↑
       Terrain + season + rainfall history
                    ↓
              Final Estimate
```

The residual is defined as:

```text
Residual = CHIRPS rainfall - calibrated rainfall
```

A separate XGBoost model predicts this residual.

However, applying the full residual produced worse overall validation performance. Therefore, a conservative correction factor was tested.

The final V1.3 correction is:

```text
Final rainfall
=
Calibrated rainfall
+
0.10 × predicted residual
```

The value `0.10` was selected using the validation period rather than the final test period.

---

# 10. V1.3 Results

Final V1.3 evaluation used the untouched 2025 test period.

## Overall rainfall performance

```text
Calibration RMSE: 7.94 mm
V1.3 RMSE:        7.88 mm

Calibration MAE:  4.59 mm
V1.3 MAE:         4.54 mm
```

Overall improvement over the calibration baseline:

```text
0.7%
```

This is a **modest improvement**, not a major breakthrough.

## Rain-event performance

```text
Hits:          849
Misses:         81
False alarms:  352

POD:           0.91
FAR:           0.29
CSI:           0.66
```

## Heavy rainfall

For rainfall ≥25 mm:

```text
Calibration RMSE: 28.32 mm
V1.3 RMSE:        28.05 mm

Calibration MAE:  26.48 mm
V1.3 MAE:         26.26 mm
```

V1.3 therefore provides a small improvement while preserving the strong general rainfall calibration.

---

# 11. Current V1.3 Model Artifacts

The current V1.3 model files are:

```text
models/v1_3_rain_calibration.pkl
models/v1_3_rain_residual.pkl
models/v1_3_metadata.pkl
models/v1_3_residual_feature_importance.csv
```

The metadata records:

```text
model_version:
    v1.3

architecture:
    linear rainfall calibration + XGBoost residual correction

target:
    CHIRPS rainfall at T+1

residual_alpha:
    0.10
```

The metadata also records the feature list, calibration inputs, temporal split, and evaluation metrics.

---

# 12. Important Data Interpretation

The rainfall datasets used in these experiments are **gridded precipitation products**.

CHIRPS is used as a historical rainfall **reference/target**, not as a direct Panchayat rain-gauge observation.

Therefore:

> TerraMind should not claim true gauge-level Panchayat rainfall accuracy unless suitable local rain-gauge/AWS observations are obtained for independent validation.

This distinction is important when presenting the project scientifically.

---

# 13. Data Pipeline

The project has progressively expanded from a basic weather pipeline into a multi-source environmental-data pipeline.

Current conceptual flow:

```text
Panchayat information
        +
Coordinates
        +
Historical weather
        +
IMD rainfall
        +
IMERG rainfall
        +
CHIRPS rainfall reference
        +
DEM / terrain
        +
River-distance information
        ↓
Feature engineering
        ↓
ML training dataset
        ↓
Model training
        ↓
Forecast / estimation engine
        ↓
Agricultural advisory
        ↓
Dashboard
```

Important data-generation scripts include:

```text
data/build_panchayats.py
data/make_coordinates.py
data/get_boundaries.py
data/get_elevation.py
data/get_river_features.py
data/merge_river_features.py
data/build_ml_dataset.py

data/build_terrain_features.py
data/extract_imd_rainfall.py
data/build_imerg_dataset.py
data/download_imerg.py
data/build_chirps_dataset.py
data/compare_chirps_spatial.py

data/build_v1_2_dataset.py
data/evaluate_v1_2.py
data/evaluate_rainfall_baselines.py
data/test_v1_3_residual_strength.py
```

Large external/raw datasets are intentionally excluded from Git where appropriate.

---

# 14. Project Structure

```text
SIH_Panchayat_Project/
│
├── data/
│   ├── raw/
│   │   ├── historical_weather.csv
│   │   ├── ml_training_dataset.csv
│   │   ├── panchayat_coordinates.csv
│   │   ├── panchayat_features.csv
│   │   ├── panchayat_river_features.csv
│   │   └── ...
│   │
│   ├── build_ml_dataset.py
│   ├── build_panchayats.py
│   ├── download_weather.py
│   ├── get_boundaries.py
│   ├── get_elevation.py
│   ├── get_river_features.py
│   ├── make_coordinates.py
│   ├── merge_river_features.py
│   ├── build_terrain_features.py
│   ├── extract_imd_rainfall.py
│   ├── build_imerg_dataset.py
│   ├── download_imerg.py
│   ├── build_chirps_dataset.py
│   ├── build_v1_2_dataset.py
│   └── ...
│
├── models/
│   ├── v1_rain_classifier.pkl
│   ├── v1_rain_regressor.pkl
│   ├── v1_tmax_regressor.pkl
│   ├── v1_3_rain_calibration.pkl
│   ├── v1_3_rain_residual.pkl
│   ├── v1_3_metadata.pkl
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── advisor.py
├── api.py
├── forecast_engine.py
├── rules.yaml
│
├── train_pipeline.py
├── train_pipeline_v1.py
├── train_pipeline_v1_2.py
├── train_pipeline_v1_3.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 15. Backend Components

## `api.py`

Main backend API. It connects the frontend with the forecasting and advisory system.

## `forecast_engine.py`

Responsible for loading trained models and generating forecast/estimation values.

## `advisor.py`

Converts forecast information into agricultural recommendations.

## `rules.yaml`

Contains configurable advisory rules.

## Training pipelines

```text
train_pipeline.py
    ↓
older/general training reference

train_pipeline_v1.py
    ↓
original V1 baseline

train_pipeline_v1_2.py
    ↓
CHIRPS-target V1.2 experiment

train_pipeline_v1_3.py
    ↓
V1.3 calibration + residual experiment
```

---

# 16. Running the Project Locally

## Requirements

Recommended:

- Python 3.x
- Node.js + npm
- Git
- Windows / Linux / macOS

---

## Step 1 — Clone the repository

```powershell
git clone https://github.com/AKASH-GHOSHT/SIH_Panchayat_Project.git
cd SIH_Panchayat_Project
```

The repository is currently private, so the user must have access through the GitHub team/repository permissions.

---

## Step 2 — Create a Python environment

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If activation is blocked, use the virtual environment's Python executable directly.

---

## Step 3 — Install Python dependencies

```powershell
pip install -r requirements.txt
```

---

## Step 4 — Start the backend

```powershell
uvicorn api:app --reload
```

The backend URL will be printed by Uvicorn.

---

## Step 5 — Start the frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Vite will print the dashboard URL.

---

# 17. Backend + Frontend Together

Normally use two terminals.

### Terminal 1 — Backend

```powershell
cd SIH_Panchayat_Project
.venv\Scripts\Activate.ps1
uvicorn api:app --reload
```

### Terminal 2 — Frontend

```powershell
cd SIH_Panchayat_Project\frontend
npm run dev
```

Open the Vite URL shown in the terminal.

---

# 18. Example Forecast Response

The application is designed around a panchayat-specific response similar to:

```json
{
  "panchayat_id": "A1",
  "panchayat_name": "ADHATA",
  "model_version": "V1.3",
  "forecast": {
    "date": "YYYY-MM-DD",
    "rain_mm": 5.4,
    "rain_probability": 0.64,
    "tmax_c": 22.4
  }
}
```

The frontend presents these values and the advisory engine can generate an agricultural recommendation.

The exact API response may change as V2 development progresses.

---

# 19. Git / Team Development Workflow

The project uses separate development branches.

Current structure:

```text
main
│
├── v2-development
│       └── Akash / ML + backend
│
└── frontend-development
        └── Frontend teammate
```

The basic rule is:

> **Do not develop directly on `main`.**

A normal workflow is:

```text
Create / switch to your branch
        ↓
Pull latest branch changes
        ↓
Code
        ↓
Test
        ↓
git status
        ↓
git add <specific-files>
        ↓
git commit
        ↓
git push
        ↓
Pull Request
        ↓
Owner review
        ↓
Merge into main
```

### Start working

```powershell
git switch <your-branch>
git pull origin <your-branch>
```

### Save work

```powershell
git status
git add <specific-files>
git commit -m "Describe the change"
git push
```

### Create a Pull Request

On GitHub:

```text
Pull requests
    ↓
New pull request

base: main
compare: your-branch
```

Describe what changed and what was tested.

### Owner merge

The repository owner reviews:

```text
Files changed
     ↓
Code correctness
     ↓
Accidental files/secrets
     ↓
Testing
     ↓
Merge Pull Request
```

After a feature is merged, teammates can update their branch:

```powershell
git switch main
git pull origin main

git switch <your-branch>
git merge main
git push
```

Because the current private personal repository does not enforce the branch-protection rule under the current GitHub setup, this workflow is currently a **team rule**. No one should directly push to `main`.

---

# 20. Repository Safety

The repository intentionally ignores local/generated files such as:

```text
.venv/
__pycache__/
node_modules/
frontend/dist/
.env
*.log
```

Large external/gridded files are also kept outside Git where appropriate, including downloaded satellite/raster data.

### Never commit:

```text
API keys
Passwords
Earthdata credentials
.netrc files
Private tokens
.env secrets
```

If a secret has accidentally been committed, removing the local file is not sufficient. The credential should be revoked/rotated and the Git history should be treated as compromised.

---

# 21. Current Development History

The ML work so far can be summarized as:

```text
V1
│
├── Initial rainfall classifier
├── Initial rainfall regressor
└── Tmax regressor
        ↓
V1.1
│
├── Added DEM terrain features
├── Added slope/aspect/roughness
└── Tested terrain contribution
        ↓
V1.2
│
├── Investigated IMD rainfall
├── Investigated IMERG rainfall
├── Added CHIRPS 0.05° reference
├── Changed rainfall target to CHIRPS T+1
└── Used temporal train/validation/test splits
        ↓
V1.3
│
├── Multi-source rainfall calibration
├── IMERG + IMD + Open-Meteo
├── XGBoost residual correction
└── Conservative residual factor α = 0.10
```

---

# 22. What We Learned

The experiments have produced several useful conclusions.

### 1. Resolution matters

The rainfall products did not provide equal spatial differentiation.

Approximate effective spatial series in the study area:

```text
IMD       → 2
IMERG     → 3
CHIRPS    → 7
```

CHIRPS therefore provided the strongest spatial differentiation among the tested rainfall products.

### 2. Multiple rainfall products contain complementary information

In the V1.2 dataset, the strongest simple rainfall correlations with the CHIRPS target were:

```text
IMERG rainfall       ≈ 0.464
Open-Meteo rainfall  ≈ 0.453
IMD rainfall         ≈ 0.249
```

This supported the decision to experiment with multi-source calibration.

### 3. A simple calibrated model was stronger than the first XGBoost amount model

The multi-source linear calibration achieved:

```text
Test RMSE: 7.94 mm
Test MAE:  4.59 mm
```

which was better than the V1.2 XGBoost rainfall model.

### 4. Extreme rainfall remains difficult

Even after calibration, heavy rainfall remains the largest error source.

This is an important current limitation of the prototype and the main target for future research.

---

# 23. Current Limitations

TerraMind is still a prototype.

Current limitations include:

- Rainfall products are gridded references rather than direct Panchayat rain-gauge measurements.
- Heavy rainfall amounts remain difficult to estimate accurately.
- The study area contains only eight Panchayats.
- Historical training coverage is relatively limited.
- Forecast quality requires further independent validation.
- Agricultural advisory rules need domain validation.
- Production data freshness and operational forecast handling still need further development.
- The current models should not be treated as replacements for official weather services or agricultural advisories.

---

# 24. Planned V2 Development

The next development phase should focus on turning the research prototype into a more complete decision-support application.

## Forecasting

Potential directions:

```text
Better extreme-rainfall handling
Better temporal/weather features
More robust spatial modeling
Independent station validation
Prediction uncertainty / confidence
```

## Agricultural intelligence

Potential directions:

```text
Crop-specific advisories
Rainfall threshold actions
Sowing / irrigation / spraying guidance
Flood and waterlogging alerts
Improved Bengali advisory content
```

## Dashboard

Potential directions:

```text
Forecast history
Rainfall trend charts
Panchayat comparison
Risk/warning indicators
Map-based visualization
Mobile-friendly design
```

## Deployment

Potential directions:

```text
Backend deployment
Frontend deployment
Secure environment variables
Monitoring / logging
Production data refresh
```

---

# 25. Research Integrity / Evaluation Philosophy

TerraMind's ML experiments use **time-based evaluation** rather than random splitting when future prediction is being simulated.

The principle is:

```text
Past
 ↓
Training

Later historical period
 ↓
Validation

Future / held-out period
 ↓
Testing
```

This avoids using future observations as training information.

Model improvements should be accepted only when they improve validation performance and then remain useful on an untouched test period.

The project also keeps earlier model versions as baselines so that improvements can be measured rather than assumed.

---

# 26. Current V1.3 Summary

```text
Current rainfall architecture:

IMERG
   +
IMD
   +
Open-Meteo
      ↓
Linear Calibration
      ↓
Calibrated Rainfall
      +
10% XGBoost Residual Correction
      ↓
CHIRPS-referenced rainfall estimate
```

Current reported test performance:

```text
RMSE: 7.88 mm
MAE:  4.54 mm

POD:  0.91
FAR:  0.29
CSI:  0.66
```

Maximum-temperature model:

```text
Tmax RMSE: 1.58 °C
Tmax MAE:  1.20 °C
Bias:     -0.12 °C
```

These figures are research/prototype evaluation results and should not be interpreted as guaranteed operational forecast accuracy.

---

# 27. TerraMind

**TerraMind** is a panchayat-level weather intelligence and agricultural advisory prototype developed for the Smart India Hackathon project.

The long-term objective is:

```text
Localized environmental data
        +
Weather information
        +
Machine learning
        +
Agricultural rules
        ↓
Simple, actionable information
for local agricultural decision-making
```

---

## License

License information can be added when the team decides how the project will be distributed.
