# AI Context & Agent Guide — TerraMind (SIH Panchayat Project)

> **Purpose:** This file provides complete, in-depth context for AI coding assistants and autonomous agents working on this codebase. It describes system architecture, exact runtime execution flows, requirements, and operational constraints.

---

## 1. Project Overview

**TerraMind** is an AI/ML-driven decision-support prototype built for the **Smart India Hackathon (SIH)**.
* **Core Goal:** Provide localized, panchayat-level weather intelligence and actionable agricultural advisories for rural farmers instead of coarse, regional/block-level forecasts.
* **Target Region (Prototype Study Area):** 8 Panchayats in Amdanga Block, North 24 Parganas, West Bengal, India:
  * `A1`: ADHATA
  * `A2`: AMDANGA
  * `A3`: BERABERIA
  * `A4`: BODAI
  * `A5`: CHANDIGARH
  * `A6`: MARICHA
  * `A7`: SADHANPUR
  * `A8`: TARABERIA

---

## 2. Exactly How It Works (Step-by-Step Runtime Flow)

When a user opens the dashboard and interacts with the application, here is the complete end-to-end execution pipeline:

```text
[Farmer / User UI]
       │  Selects: Panchayat (e.g., A1 ADHATA), Crop (e.g., paddy), Language (bn/en)
       ▼
[React Frontend (App.jsx)]
       │  Sends HTTP Request: GET /v1/forecast?panchayat_id=A1&days=5&lang=bn&crop=paddy
       ▼
[FastAPI Router (api.py)]
       │  Validates query params and invokes forecast_panchayat_v2()
       ▼
[V2 Forecast Engine (forecast_engine_v2.py)]
       │
       ├─► 1. Location Lookup: Maps "A1" to GPS coordinates using data/panchayats.csv
       │
       ├─► 2. Weather Ingestion: Pulls forecast data (Rain mm, Prob, Tmax, Tmin, Humidity)
       │      from coarse block forecast source / Open-Meteo API
       │
       ├─► 3. Context Construction (forecast_advisory_context.py):
       │      • Soil Context: Checks panchayat soil type (e.g. non_sandy from SoilGrids)
       │      • Crop Calendar: Looks up data/crop_calendar.yaml to determine the current
       │        biological stage for the date (e.g., flowering, vegetative, harvest)
       │      • Streak Tracking: Computes consecutive dry days (rain == 0) and
       │        consecutive high humidity days (humidity > 85%)
       │
       ├─► 4. Advisory Rule Evaluation (advisory_engine.py & rules.yaml):
       │      • Evaluates condition expressions against the daily context variables
       │      • Sorts matched rules by priority (critical > high > medium > low > info)
       │      • Selects highest priority matching rule
       │      • Packages bilingual advice (Bengali text_bn + English text_en)
       │
       └─► 5. Payload Assembly: Assembles weather numbers, degradation status,
              and advisory object into a standardized JSON response
       ▼
[React UI Rendering (App.jsx & ComparisonMap.jsx)]
       │  • Renders 5 daily forecast cards (Rain, Temp, Rain Probability)
       │  • Highlights active agricultural warnings (e.g., pest alert, fertilizer guidance)
       │  • Updates Leaflet Comparison Map showing spatial differences across the 8 panchayats
```

---

## 3. What the Project Needs (Prerequisites & Dependencies)

To run, develop, or deploy this project, the following components are required:

### A. System & Runtime Prerequisites
* **Operating System:** Linux, macOS, or Windows.
* **Python:** Python 3.9+ (tested up to **Python 3.14** with flexible wheel versions).
* **Node.js:** Node.js 18+ and npm.
* **Network Access:** Internet connection required for Open-Meteo weather API sync and tile downloading in Leaflet maps.

### B. Python Dependencies (`requirements.txt`)
* `fastapi` & `uvicorn`: REST API framework and ASGI server.
* `pandas` & `numpy`: Data manipulation, streak calculations, coordinate mapping.
* `pyyaml`: Parsing `rules.yaml` and `crop_calendar.yaml`.
* `scikit-learn` & `xgboost`: Machine learning baseline and residual models.
* `joblib`: Deserializing trained `.pkl` model artifacts.
* `requests`: Fetching live external weather forecasts.

### C. Frontend Dependencies (`frontend/package.json`)
* `react` & `react-dom`: UI component tree.
* `vite`: High-performance development server and bundler.
* `leaflet` & `react-leaflet`: Interactive geographic mapping of panchayats.

### D. Critical Files Required at Runtime (Must Exist)
| File | Required By | Purpose |
|:---|:---|:---|
| `rules.yaml` | `advisory_engine.py` | Advisory rule definitions, thresholds, Bengali/English text |
| `data/panchayats.csv` | `api.py`, `forecast_engine_v2.py` | Master list of 8 panchayats with IDs and center coordinates |
| `data/crop_calendar.yaml` | `forecast_advisory_context.py` | Crop stages mapped across months for Aman paddy & vegetables |
| `data/raw/coarse_block_forecast.csv` | `forecast_engine_v2.py` | Operational fallback forecast data |
| `models/v1_rain_classifier.pkl` | `models/` | Rainfall occurrence model |
| `models/v1_tmax_regressor.pkl` | `models/` | Temperature prediction model |
| `models/v1_3_*.pkl` | `models/` | V1.3 operational rainfall calibration + residual model artifacts |

### E. Network Ports
* **Port `8000`**: FastAPI backend (`http://127.0.0.1:8000`).
* **Port `5173`**: Vite React frontend (`http://localhost:5173`).

---

## 4. Directory & Team Workspace Reference (4-Member Modular Setup)

The codebase is organized into dedicated, non-overlapping workspaces for the 4-member team to prevent merge conflicts:

### 🎨 Frontend Workspace (`frontend/`) — [Member 1: Frontend Engineer]
* **`frontend/src/App.jsx`**: Main application dashboard; handles panchayat selection, crop switching, and rendering forecast cards.
* **`frontend/src/ComparisonMap.jsx`**: Leaflet map component showing spatial differences across panchayats.
* **`frontend/src/App.css`**: Component styling and high-contrast color scheme.
* **`frontend/vite.config.js`**: Vite build configuration.

### ⚙️ Backend Workspace (`backend/` & `rules/`) — [Member 2: Backend Engineer]
* **`api.py`** (Root shim): Root entrypoint redirecting to `backend.api:app` for continuous Render cloud compatibility.
* **`backend/api.py`**: FastAPI application exposing REST endpoints (`/health`, `/v1/panchayats`, `/v1/forecast`).
* **`backend/forecast_engine_v2.py`**: Primary forecast dispatcher. Computes 5-day predictions and coordinates with the advisory layer.
* **`backend/advisory_engine.py`**: Rule evaluation engine. Loads `rules/rules.yaml` and tests conditions against contextual variables.
* **`backend/advisory_context.py`**: Data classes and builders for panchayat-specific soil, crop, and historical weather streaks.
* **`backend/forecast_advisory_context.py`**: Integrates multi-day forecast trajectories with historical context to evaluate future multi-day risks.
* **`rules/rules.yaml`**: The single source of truth for agricultural advisory rules, thresholds, priority ranking, and bilingual templates.

### 🧠 AI / ML Workspace (`ml/`) — [Member 3: AI/ML & Data Engineer]
* **`ml/pipelines/train_pipeline_v1_3.py`**: Reference training pipeline for the V1.3 calibration and residual model.
* **`ml/models/`**: Serialized `.pkl` models and feature importances (`v1_*`, `v1_3_*`, `m3_clean_*`, `v2_*`).
* **`ml/evaluations/`**: Model verification scripts (`evaluate_rainfall_baselines.py`, `evaluate_m3_spatial_downscaling.py`).

### 📊 Data Pipeline Workspace (`data_pipeline/`) — [Member 3: AI/ML & Data Engineer]
* **`data_pipeline/ingest/`**: Ingestion scripts for external weather & satellite data (`download_weather.py`, `download_imerg.py`, `extract_imd_rainfall.py`).
* **`data_pipeline/features/`**: Feature engineering scripts (`build_terrain_features.py`, `build_ml_dataset.py`, `build_humidity_context.py`).
* **`data_pipeline/metadata/`**: Master static references (`panchayats.csv`, `crop_calendar.yaml`, `crop_calendar.py`).
* **`data_pipeline/raw/`**: Raw CSVs, GeoJSONs, NetCDF files, and cache (ignored in Git).

### 🚀 DevOps, Governance & QA — [Member 4: Manager & DevOps]
* **`docs/team_roles.md`**: Team role boundaries and Git workflow guidelines.
* **`docs/model_card.md`**: Responsible AI model documentation.
* **`tests/test_advisory_context.py`**: Validates context dataclass structure and threshold calculations.
* **`tests/test_advisory_rules.py`**: Tests historical weather events against `rules.yaml` triggers.
* **`tests/test_forecast_advisories.py`**: End-to-end integration test verifying forecast to advisory pipeline output.
* **`Dockerfile`**: Render deployment container configuration.
* **`.github/workflows/protect-main.yml`**: CI guard restricting direct pushes to `main`.

---

## 5. Operational State: The "Degraded" Fallback

When querying `/v1/forecast`, the API returns `"degraded": true`:
```json
{
  "degraded": true,
  "degraded_reason": "Operational five-day Panchayat-level ML downscaling is not yet validated. Coarse block forecast is used as the safe rainfall fallback."
}
```
* **Why:** The project policy explicitly prioritizes scientific honesty over unsupported claims. While experimental ML models exist, spatial validation showed that downscaling models did not reliably differentiate 5-day rainfall at hyper-local panchayat boundaries.
* **Agent Rule:** Do **not** remove or hide the `degraded` flag unless a validated operational multi-day ML model is deployed.

---

## 6. Advisory Rules System (`rules.yaml`)

Each rule contains:
```yaml
- id: "heavy_rain"
  priority: "high"         # critical > high > medium > low > info
  type: "warning"          # alert | warning | action | info
  condition: "rain_mm > 20"
  text_en: "Heavy rain expected..."
  text_bn: "ভারী বৃষ্টির সম্ভাবনা..."
```
* Variables accessible in rule conditions:
  * `rain_mm`: Expected daily rainfall (mm).
  * `rain_probability`: Probability of rain (0.0 to 1.0).
  * `tmax_c` / `tmin_c`: Maximum and minimum temperatures (°C).
  * `crop`: Currently selected crop (`paddy`, `vegetables`).
  * `stage`: Current crop growth stage (`flowering`, `harvest`, `vegetative`, etc.).
  * `soil`: Classified soil category (`sandy`, `non_sandy`).
  * `humidity_days`: Consecutive days with relative humidity > 85%.
  * `dry_days`: Consecutive days with 0 mm rainfall.

---

## 7. Development Conventions for AI Agents

1. **Bilingual Requirements:** Every agricultural advisory rule **must** provide both English (`text_en`) and Bengali (`text_bn`). Never omit Bengali text.
2. **Virtual Environment:** Python venv is at `.venv/`. Dependencies are specified in `requirements.txt` using `>=` version bounds to ensure compatibility across modern Python versions.
3. **Running Services Locally:**
   * **Backend:** `.venv/bin/uvicorn api:app --reload --host 0.0.0.0 --port 8000`
   * **Frontend:** `cd frontend && npm run dev`
4. **Git Discipline:**
   * Never commit raw raster/satellite files (`.nc`, `.nc4`, `.tif`, `.bin`).
   * Keep large experimental ML model dumps (`models/m3_*`, `models/v2_*`) out of Git.
   * Line endings are governed by `.gitattributes` (enforce LF).
5. **Testing:**
   * Run existing test suites: `pytest tests/` or directly:
     ```bash
     python tests/test_advisory_context.py
     python tests/test_advisory_rules.py
     python tests/test_forecast_advisories.py
     ```
