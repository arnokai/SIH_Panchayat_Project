# TerraMind V2 — Panchayat-Level Weather Intelligence & Agricultural Advisory

[![Frontend](https://img.shields.io/badge/Frontend-Vercel%20Live-black?style=flat&logo=vercel)](https://sih-panchayat-project.vercel.app)
[![Backend](https://img.shields.io/badge/Backend-Render%20Live-46E3B7?style=flat&logo=render)](https://sih-panchayat-project.onrender.com)
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-85EA2D?style=flat&logo=swagger)](https://sih-panchayat-project.onrender.com/docs)
[![CI Guard](https://img.shields.io/badge/CI%20Guard-Active-brightgreen?style=flat&logo=githubactions)](https://github.com/arnokai/SIH_Panchayat_Project/actions)
[![Data Lake](https://img.shields.io/badge/Data%20Lake-2.44M%20Rows%20(Parquet)-blue)](data_pipeline/processed/statewide)
[![Tests](https://img.shields.io/badge/Tests-157%20Passing-brightgreen)](tests)

> 🌐 **Live Web Application:** [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)  
> ⚡ **Live Cloud API:** [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)  
> 📚 **Interactive Swagger Docs:** [https://sih-panchayat-project.onrender.com/docs](https://sih-panchayat-project.onrender.com/docs)  
> **Repository:** `https://github.com/arnokai/SIH_Panchayat_Project`  
> **Geographic Scope:** Statewide West Bengal (3,339 Gram Panchayats across all 22 Rural Districts)  

TerraMind V2 extends the earlier V0/V1/V1.3 work into a complete, cloud-deployed **downscaling data lake, forecast engine, and agricultural-advisory decision-support system**.

---

## 🚀 Quick Start

### Requirements
- Python 3.9+ (tested on Python 3.14)
- Node.js + npm
- Git

### Step 1 — Clone the repo

```bash
git clone https://github.com/arnokai/SIH_Panchayat_Project.git
cd SIH_Panchayat_Project
```

### Step 2 — Set up Python environment

```bash
# Linux / macOS (Bash / Zsh)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```fish
# Linux / macOS (Fish shell)
python3 -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements.txt
```

```powershell
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 3 — Start the backend

```bash
# With venv activated:
uvicorn api:app --reload

# Or directly without activating (works in any shell):
.venv/bin/uvicorn api:app --reload
```

Backend runs at: **http://127.0.0.1:8000**
API docs at: **http://127.0.0.1:8000/docs**

### Step 4 — Start the frontend (new terminal)

```bash
cd frontend
npm install

# Optional: To connect your local frontend to the live Render cloud backend:
# echo "VITE_API_BASE_URL=https://sih-panchayat-project.onrender.com" > .env

npm run dev
```

Dashboard runs at: **http://localhost:5173**

---

## 1. What Changed in V2?

The main V2 change is a move from a primarily model-centric prototype toward a **decision-support pipeline**:

```text
Panchayat
   ↓
Forecast input
   ↓
5-day forecast delivery
   ↓
Forecast context builder
   ↓
Crop calendar + soil context
   ↓
Rule engine
   ↓
English advisory
   ↓
FastAPI
   ↓
React dashboard + Panchayat comparison map
```

### V2 adds

| Area | V1 / V1.3 | V2 |
|---|---|---|
| Forecast delivery | Earlier model experiments | 5-day forecast API |
| Panchayat selection | Basic | Panchayat-specific V2 API + dashboard |
| Agricultural logic | Basic rules | Context-aware advisory engine |
| Crop context | Limited | Crop + crop-stage lookup |
| Soil context | Earlier feature experiments | SoilGrids-derived soil classification |
| Dry spell logic | Not operationalized | Forecast-aware dry-day context |
| Humidity context | Earlier weather data | Consecutive high-humidity context available for advisory rules |
| Advisory language | English | English API output |
| Crop selection | Limited | `paddy` / `vegetables` in dashboard |
| Map | Earlier dashboard concept | Panchayat comparison map |
| API status | Prototype API | V2 `/v1/...` endpoints |
| Model downscaling | Multiple experimental models | Operational Two-Stage Hurdle V2 (P10/P50/P90) with safe fallback |

---

# 2. Statewide V2 AI Hurdle Downscaling Architecture

TerraMind V2 promotes a high-accuracy **Two-Stage Hurdle Downscaling Model** (`ml/models/statewide_hurdle_v2.pkl`) to operational forecasting across all 3,339 Gram Panchayats of West Bengal.

### Model Architecture & Key Metrics:
- **Stage 1 (Precipitation Occurrence):** `HistGradientBoostingClassifier` trained on 16 atmospheric, terrain, and soil features, achieving **99.39% accuracy**, **0.9999 ROC-AUC**, and **99.49% Probability of Detection (POD)**.
- **Stage 2 (Precipitation Amount):** `HistGradientBoostingRegressor` ($P_{50}$ Median) trained on rainy occurrences, achieving an MAE of **0.56 mm** and RMSE of **1.71 mm** on the untouched 2025 holdout horizon.
- **Stage 3 (Quantile Uncertainty Bounds):** Dual quantile regressors predicting $P_{10}$ (dry bound) and $P_{90}$ (flood risk bound) with **100% quantile monotonicity** ($P_{90} \ge P_{50} \ge P_{10}$).

### Operational Delivery Status:
When the model artifact is loaded, the API reports full operational health (`degraded: false`):
```json
{
  "status": "ok",
  "service": "TerraMind Panchayat Forecast API",
  "model_version": "V2.0 Statewide Hurdle (Quantile HGB)",
  "rainfall_model": "Two-Stage Hurdle Downscaling (P10/P50/P90)",
  "statewide_coverage": "3,339 Gram Panchayats / 22 Districts",
  "live_weather_enabled": true,
  "degraded": false,
  "reason": null
}
```
If network timeouts or API limits occur during live weather extraction, the engine automatically serves cached forecasts (15-min TTL) or falls back to pre-cached `coarse_block_forecast.parquet` with explicit degraded telemetry.

---

# 3. V2 Forecast Delivery & Weather Ingestion

The V2 forecast engine pipeline:

```text
Open-Meteo Live ECMWF/GFS API (15-min TTL Cache)
        ↓
Static 14-Feature Parquet Extraction (DEM, Roughness, River, Soil)
        ↓
Two-Stage Hurdle Downscaling (Occurrence + P10/P50/P90 Quantiles)
        ↓
Bilingual Agronomic Advisory Rule Engine (rules/rules.yaml)
        ↓
FastAPI Response (/v1/forecast)
```

The forecast engine supports:
- Full statewide coverage across all 3,339 Gram Panchayats (LGD ID `WB_<gp_code>`)
- 1–5 day downscaled forecast horizon
- Multi-quantile rainfall ($P_{10}$ dry bound, $P_{50}$ median, $P_{90}$ flood risk bound)
- Rain probability ($0.0$ to $1.0$)
- Maximum & minimum temperatures
- Dynamic live weather ingestion (`live=true`, default) with 15-minute in-memory TTL cache
- Graceful offline fallback (`live=false`) to local parquet baseline
- Context-aware crop advisories in English

### Supported Panchayat Identifiers:
Supports all **3,339 official Local Government Directory (LGD) Gram Panchayats** across West Bengal using canonical LGD identifiers (`WB_<gp_code>`), with backward compatibility for Amdanga pilot aliases (`A1`–`A8`):
```text
WB_107001 → Banchukamari (Alipurduar)
WB_107778 → AMDANGA (North 24 Parganas, alias: A2)
WB_110339 → Mathurapur (South 24 Parganas)
...
(Search all 3,339 Panchayats via /v1/statewide/panchayats?search=...)
```

---

# 4. V2 Agricultural Advisory Engine

V2 separates advisory logic from the forecast engine.

Main files:

```text
backend/advisory_context.py
backend/advisory_engine.py
backend/forecast_advisory_context.py
rules/rules.yaml
data_pipeline/metadata/crop_calendar.py
data_pipeline/metadata/crop_calendar.yaml
```

### Advisory flow

```text
Forecast
   +
Panchayat context
   +
Crop
   +
Crop stage
   +
Soil type
   +
Dry/humidity context
        ↓
   Rule evaluation
        ↓
   Highest-priority matching rule
        ↓
   English advisory
```

This makes the advisory system easier to modify than hard-coding every recommendation inside the API.

---

# 5. V2 Rule Categories

The current `rules.yaml` contains the following prototype rules.

### Rainfall

```text
rain_mm > 20
→ Do not spray, do not apply urea, open field drains.
```

```text
rain_mm > 5 and rain_mm <= 20
→ Moderate-rain advisory.
```

```text
rain_mm > 0 and rain_mm <= 5
→ Light-rain advisory.
```

```text
rain_mm == 0
→ Dry-day information.
```

### Heat stress

```text
crop = paddy
stage = flowering
tmax_c > 38
→ Paddy heat-stress advisory.
```

### High humidity / disease risk

```text
humidity > 85
and humidity_days >= 3
→ Paddy blast-disease risk advisory.
```

### Dry spell

```text
soil = sandy
and dry_days >= 7
→ Irrigation advisory.
```

### Harvest rain

```text
stage = harvest
and rain_mm > 0
→ Advance harvest / covered-storage advisory.
```

> These are **prototype rules**. Thresholds and agricultural actions should be reviewed with an agriculture faculty member / KVK scientist before being described as validated recommendations.

---

# 6. Crop Calendar

V2 introduces a small crop-calendar layer:

```text
data_pipeline/metadata/crop_calendar.yaml
data_pipeline/metadata/crop_calendar.py
```

Current prototype calendar:

```text
Crop: paddy
Variety group: aman
Region: Amdanga block

Flowering:
approximately 15 Sep → 05 Oct

Harvest:
approximately 01 Nov → 15 Dec
```

The flowering window reflects the representative late-September Aman scenario used in the project design.

The calendar is a **prototype context layer**, not a fully validated local crop calendar for every Panchayat.

---

# 7. Soil Context

V2 adds soil context using SoilGrids-derived surface soil properties.

Main files:

```text
data_pipeline/features/classify_soil_context.py
data_pipeline/raw/panchayat_soil_features.parquet
data_pipeline/raw/panchayat_soil_context.parquet
```

The prototype currently classifies the eight study Panchayats conservatively.

Current result:

```text
A1 → non_sandy
A2 → non_sandy
A3 → non_sandy
A4 → non_sandy
A5 → non_sandy
A6 → non_sandy
A7 → non_sandy
A8 → non_sandy
```

Therefore the sandy-soil dry-spell rule currently does not trigger for these Panchayats.

---

# 8. Historical Advisory Context

V2 also builds historical context used by the advisory layer.

### High-humidity streaks

```text
data_pipeline/features/build_humidity_context.py
data_pipeline/raw/advisory_weather_history.parquet
```

Tracks consecutive days where:

```text
humidity_pct > 85%
```

### Dry spells

```text
data_pipeline/features/build_dry_spell_context.py
data_pipeline/raw/advisory_context_history.parquet
```

Tracks consecutive days with:

```text
rain_mm == 0
```

The forecast-aware context builder then combines the latest observed streak with future forecast rainfall instead of blindly copying the historical streak into every forecast day.

---

# 9. V2 API

Main backend:

```text
backend/api.py  (with root api.py compatibility shim)
```

Main forecast engine:

```text
backend/forecast_engine_v2.py
```

## Endpoints & Verified Curl Commands

### 1. Health & Model Status
```text
GET /health
```
```bash
curl -s http://127.0.0.1:8000/health | jq
```

### 2. Statewide Data Lake Summary
```text
GET /v1/statewide/stats
```
```bash
curl -s http://127.0.0.1:8000/v1/statewide/stats | jq
```

### 3. Statewide District Directory
```text
GET /v1/statewide/districts
```
```bash
curl -s http://127.0.0.1:8000/v1/statewide/districts | jq
```

### 4. Statewide Panchayat Autocomplete & Search
```text
GET /v1/statewide/panchayats?district={district}&search={query}&limit={n}
```
```bash
curl -s "http://127.0.0.1:8000/v1/statewide/panchayats?search=Amdanga&limit=5" | jq
```

### 5. 5-Day Downscaled Weather Forecast & Advisory
```text
GET /v1/forecast?panchayat_id={id}&days={1-5}&lang={en}&crop={crop}&live={true|false}
```
```bash
# Live dynamic forecast (LGD ID):
curl -s "http://127.0.0.1:8000/v1/forecast?panchayat_id=WB_107778&days=5&lang=en&crop=paddy&live=true" | jq

# Offline fallback forecast (Pilot alias, English):
curl -s "http://127.0.0.1:8000/v1/forecast?panchayat_id=A2&days=5&lang=en&crop=paddy&live=false" | jq
```

### 6. Interactive OpenAPI / Swagger Documentation
```text
http://127.0.0.1:8000/docs
```

---

# 10. Example V2 Forecast Response

Production multi-quantile API response (`/v1/forecast?panchayat_id=WB_107778&days=5&lang=en&crop=paddy&live=true`):

```json
{
  "panchayat_id": "WB_107778",
  "panchayat_name": "AMDANGA",
  "block_name": "AMDANGA",
  "district_name": "North 24 Parganas",
  "crop": "paddy",
  "issued_at": "2026-09-08T22:50:09+05:30",
  "model_version": "V2.0 Statewide Hurdle (Quantile HGB)",
  "rainfall_model": "Two-Stage Hurdle Downscaling (P10/P50/P90)",
  "is_live_dynamic": true,
  "source": "Open-Meteo Live API (ECMWF/GFS)",
  "degraded": false,
  "degraded_reason": null,
  "forecast": [
    {
      "date": "2026-09-09",
      "rain_mm": {
        "p10": 4.2,
        "p50": 6.8,
        "p90": 11.5
      },
      "tmax_c": {
        "p50": 31.4
      },
      "tmin_c": 26.1,
      "rain_probability": 0.85,
      "advisory": {
        "rule_id": "moderate_rain",
        "priority": "medium",
        "type": "warning",
        "text": "Moderate rain expected. Monitor field drainage and avoid unnecessary field operations.",
        "text_en": "Moderate rain expected. Monitor field drainage and avoid unnecessary field operations."
      }
    }
  ]
}
```

The exact response structure may evolve during V2 development.

---

# 11. V2 Frontend

The frontend is built with:

```text
React
Vite
React Leaflet
Leaflet
```

Main files:

```text
frontend/src/App.jsx
frontend/src/App.css
frontend/src/ComparisonMap.jsx
```

### Current dashboard capabilities

- Panchayat selector
- Crop selector
- Five-day forecast cards
- Rainfall information
- Temperature information
- Agricultural advisory (English)
- Advisory priority/type
- Panchayat comparison map
- System/degraded status
- API-driven forecast data

The comparison map is an important V2 feature because the project is intended to work at **Panchayat level rather than only block level**.

---

# 12. Running V2 Locally

## Backend terminal

From the repository root:

```bash
# Linux / macOS (Bash / Zsh)
source .venv/bin/activate
uvicorn api:app --reload
```

```fish
# Linux / macOS (Fish shell)
source .venv/bin/activate.fish
uvicorn api:app --reload
```

```bash
# Direct execution (Works in any shell without activating):
.venv/bin/uvicorn api:app --reload
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
uvicorn api:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Docs:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend terminal

Open a second terminal window:

```bash
cd frontend
npm install
npm run dev
```

Vite normally prints the local dashboard URL.

Typical address:

```text
http://localhost:5173
```

---

# 13. Fresh Laptop Setup

### Linux / macOS (Bash / Zsh)

```bash
git clone https://github.com/arnokai/SIH_Panchayat_Project.git
cd SIH_Panchayat_Project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --reload
```

### Linux / macOS (Fish shell)

```fish
git clone https://github.com/arnokai/SIH_Panchayat_Project.git
cd SIH_Panchayat_Project
python3 -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements.txt
uvicorn api:app --reload
```

### Windows PowerShell

```powershell
git clone https://github.com/arnokai/SIH_Panchayat_Project.git
cd SIH_Panchayat_Project
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn api:app --reload
```

Then in a second terminal (any OS):

```bash
cd SIH_Panchayat_Project/frontend
npm install
npm run dev
```

---

# 14. 4-Member Modular Codebase Architecture

The project is structured into dedicated, conflict-free workspaces matching the 4 team member responsibilities:

```text
SIH_Panchayat_Project/
├── frontend/                          # [Member 1: Frontend Engineer]
│   ├── src/App.jsx                    # React 18 dashboard & weather cards
│   ├── src/ComparisonMap.jsx          # Interactive Leaflet panchayat comparison map
│   ├── src/App.css                    # Component styling & high-contrast cards
│   ├── vite.config.js & package.json  # Vite dev server & dependencies
│   └── vercel.json                    # Vercel deployment configuration
│
├── backend/                           # [Member 2: Backend Engineer]
│   ├── api.py                         # FastAPI routes (/health, /v1/panchayats, /v1/forecast)
│   ├── forecast_engine_v2.py          # 5-day forecast coordinator & safe fallback dispatcher
│   ├── advisory_engine.py             # Rule matching & priority resolution engine
│   ├── advisory_context.py            # Dataclasses (soil, crop stage, streaks)
│   └── forecast_advisory_context.py   # Multi-day streak tracking (dry days, humidity streaks)
│
├── rules/                             # [Member 2: Backend & Domain Rules]
│   └── rules.yaml                     # Single source of truth for agronomic rules & advisory text
│
├── ml/                                # [Member 3: AI / ML & Data Lake Engineer]
│   ├── pipelines/train_statewide_hurdle_model.py # Statewide Two-Stage Hurdle training pipeline
│   ├── models/                        # Serialized .pkl weights (statewide_hurdle_v2.pkl, pilot models)
│   └── evaluations/                   # Evaluation and spatial verification scripts
│
├── data_pipeline/                     # [Member 3: AI / ML & Data Lake Engineer]
│   ├── make_dataset.py                # Amdanga 8-GP pilot pipeline builder (5,848 rows)
│   ├── make_statewide_dataset.py      # Full West Bengal statewide pipeline (2,440,809 rows)
│   ├── io_utils.py                    # Unified high-performance Parquet I/O engine
│   ├── metadata/                      # GP registries (statewide_panchayats.parquet, panchayats.parquet)
│   ├── features/                      # Geospatial enrichment (statewide_static_features.parquet)
│   ├── processed/                     # Processed datasets & statewide/ (22 district Parquet partitions)
│   ├── storage/                       # Data lake QA validator (qa_validator.py)
│   ├── reports/                       # QA verification reports (statewide_qa_report.md)
│   └── raw/                           # Raw weather, terrain, and soil Parquet datasets
│
├── tests/                             # [Full 157-Test Automated Verification Suite]
│   ├── test_statewide_pipeline.py     # 67 comprehensive end-to-end statewide pipeline tests
│   ├── test_statewide_registry.py     # LGD registry and spatial boundary tests
│   ├── test_statewide_geo_features.py # DEM, soil texture, and river proximity tests
│   ├── test_forecast_engine_v2.py     # 5-day coordinator, live API caching, offline fallback
│   ├── test_advisory_rules.py         # Agricultural advisory rule verification tests
│   └── test_forecast_advisories.py    # End-to-end forecast and advisory integration tests
│
├── docs/                              # [Member 4: Manager / DevOps]
│   ├── architecture/
│   │   ├── AI.md                      # AI system architecture and design
│   │   ├── DEVOPS_README.md           # DevOps roadmap, milestones, and testing guide
│   │   └── team_roles.md             # Team role boundaries and Git workflow guidelines
│   ├── roadmap/
│   │   ├── BACKEND_TODO.md            # Backend milestones and action items
│   │   ├── DEVOPS_TODO.md             # DevOps milestones and action items
│   │   ├── feature_roadmap.md         # Feature roadmap and 4-member action plan
│   │   ├── FRONTEND_TODO.md           # Frontend milestones and action items
│   │   └── ML_TODO.md                 # ML milestones and action items
│   └── specs/
│       ├── data_contract.md           # Pure Parquet data lake schema & handoff contracts
│       ├── model_card.md              # Responsible AI model documentation
│       └── statewide_requirements.md  # Statewide expansion requirements
│
└── DevOps & Root Entrypoints          # [Member 4: Manager & DevOps]
    ├── Dockerfile                     # Container definition for Render cloud deployment
    ├── .dockerignore                  # Container build exclusions
    ├── .github/workflows/protect-main.yml # GitHub Actions branch guard for main
    ├── api.py                         # Root backward-compatibility shim (delegates to backend.api:app)
    └── requirements.txt               # Pinned Python dependencies
```

---

# 14.1 Cloud Deployment Architecture

TerraMind V2 is deployed to production using a decoupled, zero-cost cloud architecture:

```text
                        ┌─────────────────────────────────────────────────────────┐
                        │                     USER BROWSER                        │
                        └──────────────────────────┬──────────────────────────────┘
                                                   │
                                    HTTPS Requests │
                                                   ▼
┌──────────────────────────────────────────────────┴──────────────────────────────────────────────────┐
│                                 Vercel Global Edge Network (Frontend)                               │
│  - React 19 + Vite Dashboard                                                                        │
│  - Interactive Leaflet Panchayat Map                                                                │
│  - Agricultural Advisories                                                                          │
│  - URL: https://sih-panchayat-project.vercel.app                                                    │
└──────────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                   │
                            API Requests           │  (VITE_API_BASE_URL)
                            [CORS Allowed]         ▼
┌──────────────────────────────────────────────────┴──────────────────────────────────────────────────┐
│                                   Render Web Service (Backend)                                      │
│  - Containerized FastAPI + Uvicorn server (Docker on port 7860)                                     │
│  - Operational statewide Two-Stage Hurdle ML model in ml/models/                                    │
│  - Live weather forecast extraction (Open-Meteo) & Soil context evaluation (SoilGrids)              │
│  - URL: https://sih-panchayat-project.onrender.com                                                  │
│  - Swagger Docs: https://sih-panchayat-project.onrender.com/docs                                    │
└──────────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               GitHub Actions CI Guard (Repository Security)                          │
│  - .github/workflows/protect-main.yml intercepts direct pushes to the `main` branch                │
│  - Rejects unauthorized direct pushes, enforcing team feature branch + PR review workflows          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Live URLs
- **Web Dashboard:** [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)
- **API Base:** [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)
- **Interactive Swagger Documentation:** [https://sih-panchayat-project.onrender.com/docs](https://sih-panchayat-project.onrender.com/docs)
- **Backend Health Check:** [https://sih-panchayat-project.onrender.com/health](https://sih-panchayat-project.onrender.com/health)

---

# 15. Operational Machine Learning Models

The repository packages the trained operational model artifacts in `ml/models/`:

```text
ml/models/statewide_hurdle_v2.pkl       # Two-Stage Hurdle Downscaling Model (1.5 MB)
                                        # Stage 1: Rain Occurrence (HGBClassifier, 99.39% acc)
                                        # Stage 2: Precipitation Amount (HGBRegressor P50, 0.56mm MAE)
                                        # Stage 3: Quantile Uncertainty (HGBRegressor P10 & P90)
ml/models/v1_rain_classifier.pkl        # Pilot rain occurrence classifier
ml/models/v1_tmax_regressor.pkl         # Pilot maximum temperature regressor
ml/models/v1_3_rain_calibration.pkl     # Multi-source linear rainfall calibration
ml/models/v1_3_rain_residual.pkl        # XGBoost residual correction model
```

> **Pre-packaged:** All operational and pilot model artifacts are bundled directly in `ml/models/` (~2.6 MB total). Anyone who clones the project can run predictions out of the box without retraining.

---

# 16. V2 Data Sources / Context

The V2 pipeline uses or prepares context from:

```text
Historical weather
Open-Meteo forecast
Panchayat coordinates
SoilGrids soil properties
Crop calendar
Humidity history
Dry-spell history
Earlier rainfall/model experiments
```

The project continues to keep large external source/raster datasets outside Git where appropriate.

---

# 17. Testing

TerraMind includes a comprehensive 157-test automated verification suite in `tests/`:

```bash
# Run complete 157-test verification suite
python -m unittest discover -s tests

# Or directly using project virtual environment
.venv/bin/python -m unittest discover -s tests
```

The test suite executes 157 unit tests across 13 test files covering registry boundaries, 14-feature physical realism, Parquet data lake Hive partition integrity, zero temporal leakage, forecast engine caching, and agronomic advisory rules in under 3 seconds.

---

# 18. Current V2 Scope & Future Enhancements

TerraMind V2 delivers statewide operational downscaling across all 3,339 Gram Panchayats.

Current operational scope:
- Full 22-district statewide coverage across 3,339 Gram Panchayats using official LGD codes.
- High-accuracy Two-Stage Hurdle Downscaling model (`statewide_hurdle_v2.pkl`) producing P10/P50/P90 quantile bounds.
- Dynamic live weather ingestion from Open-Meteo with 15-minute TTL caching and graceful offline fallback.
- Context-aware agronomic advisories (English) for major agro-climatic zones.

Future roadmap enhancements:
- Local agricultural faculty & KVK field validation of dynamic spray/irrigation thresholds.
- Real-time IoT / Automatic Weather Station (AWS) telemetry integration for micro-climate calibration.
- Surface waterlogging batch calculation combining Copernicus DEM elevation and river proximity.
- PMFBY automated crop loss verification certificates for disaster mitigation.

---

# 19. V1.3 → V2 in One View

```text
V1
│
├── Basic ML rainfall / rain probability / Tmax
│
↓
V1.1
│
├── Terrain features
│
↓
V1.2
│
├── IMD + IMERG + CHIRPS experiments
├── CHIRPS T+1 rainfall target
│
↓
V1.3
│
├── Multi-source rainfall calibration
├── Residual correction
│
↓
V2
│
├── Statewide pure Parquet lake (22 districts, 3,339 GPs, 2.44M rows)
├── Operational Two-Stage Hurdle downscaling (statewide_hurdle_v2.pkl)
├── Multi-quantile bounds (P10 dry / P50 median / P90 flood risk)
├── Live Open-Meteo ECMWF/GFS weather connector (15-min TTL cache)
├── Graceful offline fallback (live=false)
├── 5-day forecast delivery (/v1/forecast)
├── Statewide directory & search endpoints (/v1/statewide/*)
├── Context-aware agronomic advisory engine (rules/rules.yaml)
├── English advisory API
├── 3,339 GP search & comparison map
├── Render + Vercel cloud deployment with CI branch protection
└── Complete 157-test automated verification suite
```

---

# 20. Development Philosophy

V2 follows one important principle:

> **Do not claim more forecast accuracy than the validation evidence supports.**

The system should provide useful localized decision support while making the current limitations visible.

Future V2.x work can focus on:

```text
better spatial downscaling
independent station/AWS validation
stronger heavy-rainfall handling
forecast uncertainty
better local crop calendars
agriculture-domain validation
```

---

## TerraMind

**TerraMind — Understand Earth. Empower Futures.**

Panchayat-level environmental intelligence for agricultural decision support.
