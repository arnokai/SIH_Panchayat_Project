# AI Context & Agent Guide — TerraMind (SIH Panchayat Project)

> **Purpose:** This file provides complete, in-depth context for AI coding assistants and autonomous agents working on this codebase. It describes system architecture, exact runtime execution flows, requirements, and operational constraints.

---

## 1. Project Overview

**TerraMind** is an AI/ML-driven decision-support system built for the **Smart India Hackathon (SIH)** (Problem Statement SIH26074 — Ministry of Earth Sciences).
* **Core Goal:** Provide localized, panchayat-level weather intelligence and actionable agricultural advisories for rural farmers instead of coarse, regional/block-level forecasts.
* **Operational Scope:** Statewide coverage across all **3,339 Gram Panchayats** spanning 342 Community Development Blocks in all **22 rural districts** of West Bengal, India.
* **Data Architecture:** Pure Apache Parquet data lake partitioned by district (`data_pipeline/processed/statewide/district_name=*/data.parquet`, ~2.44 million rows spanning 2024–2025). Zero active CSV files.
* **AI Model:** Two-Stage Hurdle Downscaling Model with Quantile Uncertainty (`ml/models/statewide_hurdle_v2.pkl`) achieving 99.39% accuracy, 0.9999 ROC-AUC, 0.56 mm MAE, and 100% quantile monotonicity.
* **Operational Status:** Production ML active (`degraded: false`).

---

## 2. Exactly How It Works (Step-by-Step Runtime Flow)

When a user opens the dashboard and interacts with the application, here is the complete end-to-end execution pipeline:

```text
[Farmer / User UI]
       │  Selects: District, Block, Panchayat (e.g., WB_107778 AMDANGA), Crop (e.g., paddy), Language (bn/en)
       ▼
[React Frontend (App.jsx & ComparisonMap.jsx)]
       │  Sends HTTP Request: GET /v1/forecast?panchayat_id=WB_107778&days=5&lang=bn&crop=paddy&live=true
       ▼
[FastAPI Router (backend/api.py)]
       │  Validates query params and invokes forecast_panchayat_v2()
       ▼
[V2 Forecast Engine (backend/forecast_engine_v2.py)]
       │
       ├─► 1. Location Lookup & Aliasing:
       │      Resolves panchayat ID (supporting LGD codes WB_107001..WB_111115 and pilot aliases A1..A8)
       │      against data_pipeline/metadata/statewide_panchayats.parquet to get GPS coordinates and block info.
       │
       ├─► 2. Dynamic Weather Ingestion & Caching:
       │      Pulls dynamic 5-day ECMWF/GFS weather forecasts via Open-Meteo Live API with 15-minute
       │      in-memory TTL caching. Gracefully falls back to data_pipeline/raw/coarse_block_forecast.parquet
       │      if offline or network request fails.
       │
       ├─► 3. Geospatial & Edaphic Feature Lookup:
       │      Extracts static physical features for the GP from
       │      data_pipeline/features/statewide_static_features.parquet (14-column contract: elevation,
       │      slope, aspect sin/cos, roughness, relative elevation, river distance, sand/clay/silt %).
       │
       ├─► 4. Two-Stage Hurdle ML Downscaling (ml/models/statewide_hurdle_v2.pkl):
       │      • Constructs 16-feature vector (3 coarse weather + 6 terrain + 1 hydro + 3 soil + 3 seasonal).
       │      • Stage 1 (HistGradientBoostingClassifier): Computes rain probability P(rain).
       │      • Hurdle Decision: If P(rain) >= 0.35, activates Stage 2 & 3 regressors; else outputs 0.0 mm.
       │      • Stage 2 (HistGradientBoostingRegressor): Computes expected P50 median rain amount.
       │      • Stage 3 (Quantile Regressors): Computes P10 (dry bound) and P90 (flood risk bound).
       │      • Enforces strict physical monotonicity: 0.0 <= P10 <= P50 <= P90.
       │
       ├─► 5. Context Construction (backend/forecast_advisory_context.py):
       │      • Soil Context: Evaluates sandy vs non-sandy soil from static features.
       │      • Crop Calendar: Evaluates current biological stage from data_pipeline/metadata/crop_calendar.yaml.
       │      • Streak Tracking: Computes consecutive dry days and humidity streaks.
       │      • Passes downscaled P50 rainfall as daily precipitation context.
       │
       ├─► 6. Advisory Rule Evaluation (backend/advisory_engine.py & rules/rules.yaml):
       │      • Evaluates condition expressions against daily context variables.
       │      • Sorts matched rules by priority (critical > high > medium > low > info).
       │      • Selects highest priority matching rule and packages bilingual advice (text_bn + text_en).
       │
       └─► 7. Payload Assembly:
              Assembles weather quantiles, dynamic live status, degraded flag (false), and advisories
              into standardized UTF-8 JSON response.
       ▼
[React UI Rendering (App.jsx & ComparisonMap.jsx)]
       │  • Renders 5 daily forecast cards (Rain P10/P50/P90, Temp, Rain Probability, Live Badge).
       │  • Highlights active agricultural warnings (e.g., blast disease alert, fertilizer guidance).
       │  • Updates interactive Leaflet map displaying statewide panchayats and micro-climate gradients.
```

---

## 3. What the Project Needs (Prerequisites & Dependencies)

To run, develop, or deploy this project, the following components are required:

### A. System & Runtime Prerequisites
* **Operating System:** Linux, macOS, or Windows.
* **Python:** Python 3.10+ (tested up to **Python 3.14** with flexible wheel versions).
* **Node.js:** Node.js 18+ and npm.
* **Network Access:** Internet connection required for Open-Meteo live dynamic forecast sync and Leaflet map tiles.

### B. Python Dependencies (`requirements.txt`)
* `fastapi` & `uvicorn`: REST API framework and ASGI server.
* `pandas`, `numpy` & `pyarrow`: Data manipulation, streak calculations, coordinate mapping, and Parquet I/O.
* `pyyaml`: Parsing `rules/rules.yaml` and `crop_calendar.yaml`.
* `scikit-learn`: Machine learning classifier and quantile regression models (`HistGradientBoosting`).
* `joblib`: Deserializing trained `.pkl` model artifacts.
* `requests`: Fetching live external weather forecasts from Open-Meteo.

### C. Frontend Dependencies (`frontend/package.json`)
* `react` & `react-dom`: UI component tree.
* `vite`: High-performance development server and bundler.
* `leaflet` & `react-leaflet`: Interactive geographic mapping of panchayats.

### D. Critical Files Required at Runtime (Must Exist)
| File | Required By | Purpose |
|:---|:---|:---|
| `rules/rules.yaml` | `backend/advisory_engine.py` | Advisory rule definitions, thresholds, Bengali/English text |
| `data_pipeline/metadata/statewide_panchayats.parquet` | `backend/forecast_engine_v2.py`, `backend/api.py` | Master catalog of 3,339 Gram Panchayats with LGD codes and GPS |
| `data_pipeline/features/statewide_static_features.parquet` | `backend/forecast_engine_v2.py` | 14-column physical static features (terrain, soil, rivers) |
| `data_pipeline/metadata/crop_calendar.yaml` | `backend/forecast_advisory_context.py` | Crop stages mapped across months for Aman paddy & vegetables |
| `data_pipeline/raw/coarse_block_forecast.parquet` | `backend/forecast_engine_v2.py` | Offline fallback weather forecast data |
| `ml/models/statewide_hurdle_v2.pkl` | `backend/forecast_engine_v2.py` | Trained Two-Stage Hurdle Downscaling Model with Quantiles |

### E. Network Ports
* **Port `8000`**: FastAPI backend (`http://127.0.0.1:8000`).
* **Port `5173`**: Vite React frontend (`http://localhost:5173`).

---

## 4. Directory & Team Workspace Reference (4-Member Modular Setup)

The codebase is organized into dedicated, non-overlapping workspaces for the 4-member team to prevent merge conflicts:

### 🎨 Frontend Workspace (`frontend/`) — [Member 1: Frontend Engineer]
* **`frontend/src/App.jsx`**: Main application dashboard; handles statewide panchayat search, crop switching, and rendering forecast cards.
* **`frontend/src/ComparisonMap.jsx`**: Leaflet map component showing spatial differences across panchayats.
* **`frontend/src/App.css`**: Component styling and high-contrast color scheme.
* **`frontend/vite.config.js`**: Vite build configuration.

### ⚙️ Backend Workspace (`backend/` & `rules/`) — [Member 2: Backend Engineer]
* **`api.py`** (Root shim): Root entrypoint redirecting to `backend.api:app` for continuous Render cloud compatibility.
* **`backend/api.py`**: FastAPI application exposing REST endpoints (`/health`, `/v1/forecast`, `/v1/statewide/panchayats`, `/v1/statewide/districts`, `/v1/statewide/stats`).
* **`backend/forecast_engine_v2.py`**: Primary forecast dispatcher. Integrates dynamic Open-Meteo weather with static features and the Hurdle ML downscaler.
* **`backend/advisory_engine.py`**: Rule evaluation engine. Loads `rules/rules.yaml` and tests conditions against contextual variables.
* **`backend/advisory_context.py`**: Data classes and builders for panchayat-specific soil, crop, and historical weather streaks.
* **`backend/forecast_advisory_context.py`**: Integrates multi-day forecast trajectories with historical context to evaluate future multi-day risks.
* **`rules/rules.yaml`**: The single source of truth for agricultural advisory rules, thresholds, priority ranking, and bilingual templates.

### 🧠 AI / ML Workspace (`ml/`) — [Member 3: AI/ML & Data Engineer]
* **`ml/pipelines/train_statewide_hurdle_model.py`**: Active statewide 550k-row Two-Stage Hurdle + Quantile training pipeline.
* **`ml/models/statewide_hurdle_v2.pkl`**: Active operational Two-Stage Hurdle artifact with P10/P50/P90 quantile models (1.54 MB).
* **`ml/evaluations/`**: Model verification scripts (`evaluate_rainfall_baselines.py`, `evaluate_m3_spatial_downscaling.py`).

### 📊 Data Pipeline Workspace (`data_pipeline/`) — [Member 3: AI/ML & Data Engineer]
* **`data_pipeline/make_statewide_dataset.py`**: Master statewide 2.44M-row dataset generator.
* **`data_pipeline/features/statewide_geo_features.py`**: 14-column physical static feature extraction engine.
* **`data_pipeline/features/statewide_static_features.parquet`**: Master static physical features dataset for all 3,339 Gram Panchayats.
* **`data_pipeline/metadata/build_statewide_registry.py`**: Statewide LGD GP catalog builder.
* **`data_pipeline/metadata/statewide_panchayats.parquet`**: Master 3,339 Gram Panchayat registry.
* **`data_pipeline/processed/statewide/`**: Pure Parquet data lake partitioned by `district_name=*` (731 continuous days, 2,440,809 rows).

### 🚀 DevOps, Governance & QA — [Member 4: Manager & DevOps]
* **`docs/architecture/team_roles.md`**: Team role boundaries and Git workflow guidelines.
* **`docs/specs/model_card.md`**: Responsible AI model documentation.
* **`tests/test_advisory_context.py`**: Validates context dataclass structure and threshold calculations.
* **`tests/test_advisory_rules.py`**: Tests historical weather events against `rules.yaml` triggers.
* **`tests/test_forecast_advisories.py`**: End-to-end integration test verifying forecast to advisory pipeline output.
* **`Dockerfile`**: Render deployment container configuration.
* **`.github/workflows/protect-main.yml`**: CI guard restricting direct pushes to `main`.

---

## 5. Operational State: Live Machine Learning (`degraded: false`)

When querying `/v1/forecast`, the API returns `"degraded": false` under normal operation:
```json
{
  "degraded": false,
  "degraded_reason": null,
  "model_version": "V2.0 Statewide Hurdle (Quantile HGB)",
  "rainfall_model": "Two-Stage Hurdle Downscaling (P10/P50/P90)",
  "is_live_dynamic": true
}
```
* **Why:** The statewide Two-Stage Hurdle downscaling model (`statewide_hurdle_v2.pkl`) is fully validated across a 550,000-row stratified dataset over 22 districts, achieving 99.39% accuracy, 0.9999 ROC-AUC, 0.56 mm MAE, and 100% quantile monotonicity.
* **Fallback Policy:** If `statewide_hurdle_v2.pkl` or static feature files are missing or unreadable, the engine automatically falls back to coarse block forecast data and safely sets `"degraded": true` with an explanatory reason. Under normal conditions, `"degraded": false` is returned.

---

## 6. Advisory Rules System (`rules/rules.yaml`)

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
2. **Pure Parquet Data Lake:** Never commit or depend on active CSV files in `data_pipeline/`. Use partitioned Apache Parquet (`pyarrow` / `fastparquet`).
3. **Running the Full Test Suite:**
   ```bash
   .venv/bin/python -m unittest discover -s tests
   ```
   *All 157 unit tests must pass with exit code 0.*
4. **Running Services Locally:**
   * **Backend:** `.venv/bin/uvicorn api:app --reload --host 0.0.0.0 --port 8000`
   * **Frontend:** `cd frontend && npm run dev`
5. **Git Discipline:**
   * Never commit raw raster/satellite files (`.nc`, `.nc4`, `.tif`, `.bin`).
   * Keep large experimental ML model dumps (`models/m3_*`, `models/v2_*`) out of Git.
   * Line endings are governed by `.gitattributes` (enforce LF).
