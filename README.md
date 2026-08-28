# TerraMind — Panchayat-Level Weather Intelligence & Agricultural Advisory

TerraMind is a prototype decision-support system designed to provide **panchayat-level weather forecasts and agricultural advisories**.

The current V1 prototype combines historical weather information with panchayat/terrain features and trained machine-learning models to estimate:

- 🌧️ Rainfall
- ☔ Rain probability
- 🌡️ Maximum temperature
- 🌱 Rule-based agricultural advisory
- 🇮🇳 English + Bengali advisory text

> **Project status:** V1 prototype / development stage  
> **Model version:** `gbt-v1.0`

---

## 1. What TerraMind Does

Instead of giving only a general weather forecast, TerraMind is designed around the needs of a specific panchayat.

The system follows this basic flow:

```text
Panchayat
    ↓
Panchayat + terrain/weather features
    ↓
ML Forecast Engine
    ↓
Rainfall + Rain Probability + Tmax
    ↓
Agricultural Advisory Rules
    ↓
Web Dashboard
```

The current prototype uses three trained V1 models:

```text
Rain Classifier      → probability of rain
Rain Regressor       → predicted rainfall (mm)
Tmax Regressor       → predicted maximum temperature (°C)
```

The agricultural advisory layer then converts the forecast into a simple action-oriented recommendation.

---

## 2. Main Features

### Weather Forecast

For a selected panchayat, the dashboard displays:

- Predicted rainfall in mm
- Probability of rain
- Maximum temperature
- Forecast date
- Model status/version

### Agricultural Advisory

The advisory engine uses rule-based logic from `rules.yaml`.

It can produce:

- Priority level
- Advisory type
- English recommendation
- Bengali recommendation
- Advisory rule ID

Example:

```text
Light rain. Safe to apply light fertilisers.

হালকা বৃষ্টি। সার প্রয়োগ করা নিরাপদ।
```

### Panchayat-Level Data

The data pipeline contains scripts for:

- Panchayat construction
- Coordinates
- Weather data
- Elevation
- River features
- Feature merging
- ML dataset construction

---

# 3. Project Structure

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
│   └── panchayats.csv
│
├── models/
│   ├── v1_rain_classifier.pkl
│   ├── v1_rain_regressor.pkl
│   └── v1_tmax_regressor.pkl
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
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 4. Backend Components

### `api.py`

Main backend API.

It connects the frontend with the forecasting/advisory system.

### `forecast_engine.py`

Responsible for loading the trained ML models and generating forecast values.

### `advisor.py`

Responsible for converting forecast information into agricultural advice.

### `rules.yaml`

Contains the rule configuration used by the advisory engine.

### `train_pipeline_v1.py`

Training pipeline for the current V1 models.

### `train_pipeline.py`

Older/general training pipeline retained for development/reference.

---

# 5. Machine Learning Models

The current V1 prototype contains:

| Model | Purpose | Output |
|---|---|---|
| `v1_rain_classifier.pkl` | Rain classification | Rain probability |
| `v1_rain_regressor.pkl` | Rainfall regression | Rainfall in mm |
| `v1_tmax_regressor.pkl` | Temperature regression | Tmax in °C |

The models are currently stored directly in the repository so that teammates can clone the project and test the prototype without retraining everything first.

---

# 6. Data Pipeline

The data preparation process is organized inside `data/`.

Conceptually:

```text
Panchayat information
        +
Coordinates
        +
Historical weather
        +
Elevation
        +
River/terrain features
        ↓
Feature dataset
        ↓
ML training dataset
        ↓
V1 models
```

The repository currently contains prepared datasets required by the prototype.

The external river source dataset is intentionally excluded from Git because it is a large external source dataset and can be obtained separately if needed.

---

# 7. Running the Project Locally

## Requirements

Recommended environment:

- Windows / Linux / macOS
- Python 3.x
- Node.js + npm
- Git

---

## Step 1 — Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd SIH_Panchayat_Project
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with the repository URL shown by GitHub.

---

## Step 2 — Create the Python virtual environment

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, the Python environment can also be used without activating it by calling its executables directly.

---

## Step 3 — Install Python dependencies

```powershell
pip install -r requirements.txt
```

---

## Step 4 — Start the backend

The backend is implemented in `api.py`.

If the project is using the FastAPI/Uvicorn setup configured in the current prototype:

```powershell
uvicorn api:app --reload
```

The API should then be available locally through the address printed by Uvicorn.

> If the backend configuration changes during development, update this section together with the API entry point.

---

# 8. Running the Frontend

Open a **second terminal**.

Go to the frontend:

```powershell
cd frontend
```

Install JavaScript dependencies:

```powershell
npm install
```

Start the Vite development server:

```powershell
npm run dev
```

Vite will print the local dashboard URL in the terminal.

Open that URL in a browser.

---

# 9. Running Backend + Frontend Together

You normally need two terminals.

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

Then open the frontend URL shown by Vite.

---

# 10. Testing a Panchayat

The dashboard allows a panchayat to be selected.

The backend returns forecast information similar to:

```json
{
  "panchayat_id": "A1",
  "panchayat_name": "ADHATA",
  "model_version": "gbt-v1.0",
  "forecast": {
    "date": "2026-01-01",
    "rain_mm": 5.4,
    "rain_probability": 0.64,
    "tmax_c": 22.4
  }
}
```

The frontend then presents these values through the dashboard and displays an agricultural advisory when the rule engine produces one.

---

# 11. Important Development Note

The current project is a **prototype**, not yet a production weather service.

In particular:

- Forecast quality still needs proper validation.
- Model performance needs to be evaluated with suitable train/test methodology.
- Rainfall, rain probability, and temperature predictions should be validated against appropriate historical observations.
- Advisory rules need domain validation before real agricultural deployment.
- Data freshness and forecast-date handling need further development.
- The system should not be treated as a replacement for official weather or agricultural advisories.

---

# 12. Current V1 Scope

The current V1 focuses on establishing the core pipeline:

```text
Data
 ↓
Features
 ↓
ML Models
 ↓
Forecast API
 ↓
Advisory Engine
 ↓
Web Dashboard
```

The goal at this stage is to make this pipeline reliable and understandable before adding more advanced features.

---

# 13. Planned Development

The next development stages are expected to focus on:

### Phase 1 — Stabilize V1

- Verify API responses
- Verify frontend/API integration
- Validate model outputs
- Fix inconsistent forecast behaviour
- Test multiple panchayats
- Clean unused/backup code where appropriate

### Phase 2 — Improve Forecasting

- Better feature engineering
- Better temporal/weather features
- Proper validation metrics
- Model comparison
- Forecast confidence handling
- Improved rainfall prediction

### Phase 3 — Improve Agricultural Intelligence

- Expand `rules.yaml`
- Add crop-specific recommendations
- Add rainfall thresholds
- Add farming-action recommendations
- Improve Bengali advisory content

### Phase 4 — Improve Dashboard

- Better visualizations
- Forecast history
- Trend information
- Panchayat comparison
- Clearer warnings/priorities
- Mobile-friendly UI

### Phase 5 — Deployment

- Deploy backend
- Deploy frontend
- Configure production environment
- Add secure environment variables where required
- Add monitoring/logging
- Make the application accessible to users outside the development machine

---

# 14. Collaboration

This repository is intended to be shared with the TerraMind development team.

Typical workflow:

```bash
git pull
```

Create/update code, then:

```bash
git status
git add .
git commit -m "Describe your change"
git push
```

Before starting major work, pull the latest changes:

```bash
git pull
```

For larger features, use a separate Git branch rather than directly changing `main`.

Example:

```bash
git checkout -b feature/new-advisory
```

After completing the feature, push the branch:

```bash
git push -u origin feature/new-advisory
```

Then create a Pull Request on GitHub.

---

# 15. Repository Safety

The repository intentionally ignores:

```text
.venv/
node_modules/
.env
*.log
frontend/dist/
```

It also excludes the older V0 model files and the large external river source dataset.

**Never commit API keys, passwords, private tokens, or other secrets.**

If a secret is accidentally committed, removing it from the working directory is not enough; the Git history may still contain it and it should be rotated/revoked.

---

# 16. TerraMind

**TerraMind** is a panchayat-level weather intelligence and agricultural advisory prototype developed for the SIH project.

The long-term objective is to turn localized environmental and weather data into **simple, actionable information for agricultural decision-making**.

---

## License

License information can be added when the team decides how the project will be distributed.
