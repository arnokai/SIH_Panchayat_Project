# TerraMind DevOps, Architecture & Project Management Guide

> **Assigned Owner:** Member 4 — Project Manager & DevOps  
> **Workspaces:** Root, `.github/`, `docs/`, `tests/`  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Live Deployments:**
> - 🌐 Frontend: [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)
> - ⚡ Backend: [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)
> - 📚 Swagger Docs: [https://sih-panchayat-project.onrender.com/docs](https://sih-panchayat-project.onrender.com/docs)
> **Status:** Pure Parquet lake complete (2.44M rows, 22 districts). Two-Stage Hurdle model V2 operational (`degraded: false`). Live dynamic weather API integration active. All 157 unit tests passing.

---

## 1. Executive Summary & Role Mission

As the **Project Manager & DevOps Engineer (Member 4)**, you ensure uninterrupted system uptime, automated CI/CD validation, zero-friction developer coordination across the team roles, disaster recovery, and hackathon presentation delivery:
1. **Cloud Deployments & Infrastructure:** Managing production hosting on Vercel and Render with auto-deployment triggers, zero downtime, and health checks (`/health` returning `degraded: false`).
2. **Automated CI/CD Quality Guards (`.github/workflows/`):** Enforcing automated test execution and preventing broken code from merging into `main`.
3. **Automated Data Lake QA Engine:** Maintaining statewide partitioned data lake validation and zero data leakage.
4. **Automated Data Ingestion Schedulers:** Configuring automated cron jobs (daily 05:30 IST) to ingest fresh weather data and trigger pre-cached panchayat advisories.
5. **Offline Demo Contingency (Docker):** Building a self-contained, 1-command Docker container so the entire application can run offline during judging if venue Wi-Fi fails.
6. **SIH Compliance & Presentation Management:** Managing the official 6-slide presentation deck, risk mitigation tables, and jury defense strategy.

---

## 2. Completed Engineering Milestones

- [x] **Pure Parquet Statewide Data Lake Migration:**
  - Eradicated all active CSV dependencies from data processing pipelines.
  - Partitioned 2,440,809 records into 22 district Hive partitions (`data_pipeline/processed/statewide/district_name=*/data.parquet`).
  - Verified 3,339 unique Gram Panchayats over 731 continuous days (`2024-01-01` to `2025-12-31`) with zero duplicate keys and zero NaNs.
- [x] **Automated Data Lake QA Engine:**
  - Developed `data_pipeline/storage/qa_validator.py` and published `data_pipeline/reports/statewide_qa_report.md` confirming 100% integrity pass.
- [x] **157-Test Automated Verification Suite:**
  - Expanded test coverage across 13 test files in `tests/` validating registry boundaries, geospatial features, physical realism, pipeline leakage, forecast engine, and advisory rules in under 3 seconds.
- [x] **Two-Stage Hurdle Model Deployment:**
  - Trained and integrated `ml/models/statewide_hurdle_v2.pkl` (99.39% accuracy, 0.9999 ROC-AUC, MAE 0.56 mm), delivering $P_{10}$, $P_{50}$, and $P_{90}$ precipitation bounds and clearing `degraded: false`.
- [x] **Live Dynamic Weather Connector:**
  - Implemented real-time Open-Meteo ECMWF/GFS fetcher with 15-minute in-memory TTL caching and graceful offline fallback in `backend/forecast_engine_v2.py`.
- [x] **Production Cloud Deployment & Root Shim:**
  - Configured root `api.py` delegation shim guaranteeing seamless Render cloud deployments alongside Vercel SPA hosting.
- [x] **Main Branch Protection:**
  - Active GitHub Actions workflow `.github/workflows/protect-main.yml` blocking unauthorized direct pushes to `main`.

---

## 3. Directory Layout & Workspace Ownership

```text
.
├── .github/
│   └── workflows/
│       ├── protect-main.yml         # CI workflow: guards main against unauthorized direct pushes
│       └── daily-weather-sync.yml   # (In Development) Daily 05:30 IST weather ingestion cron
├── docs/
│   ├── team_roles.md                # 4-member workspace division and git branch rules
│   ├── model_card.md                # Scientific model documentation & metrics
│   ├── data_contract.md             # Pure Parquet data lake schema & handoff contracts
│   ├── statewide_requirements.md    # Statewide acceptance criteria & verification log
│   └── DEVOPS_README.md             # (This DevOps guide & roadmap)
├── tests/                           # 157-test automated verification suite (13 test files)
│   ├── test_statewide_pipeline.py   # 67 statewide Parquet lake tests
│   ├── test_statewide_registry.py   # Geographic boundary & LGD tests
│   ├── test_statewide_geo_features.py # DEM, SoilGrids, river proximity tests
│   ├── test_forecast_engine_v2.py   # 5-day coordinator, live API caching, offline fallback
│   ├── test_advisory_rules.py       # Rule evaluation against 5,848 historical weather rows
│   └── ...                          # Challenger & integration test suites
├── Dockerfile                       # Multi-stage production container (Python 3.11-slim)
├── docker-compose.yml               # (In Development) Local offline stack (Backend + Frontend)
├── requirements.txt                 # Backend & ML Python dependencies
├── vercel.json                      # Vercel SPA routing rules
└── docs/roadmap/DEVOPS_TODO.md       # DevOps action checklist
```

---

## 4. Active Roadmap & Task Checklist

### Phase 1: Automated Scheduled Data Ingestion (Cron / GitHub Actions)
- [ ] **1.1 Daily Forecast Sync Workflow (`.github/workflows/daily-weather-sync.yml`):**
  - Configure scheduled GitHub Actions cron:
    ```yaml
    name: Daily Weather Ingestion
    on:
      schedule:
        - cron: '0 0 * * *' # Runs at 05:30 IST (00:00 UTC) every morning
      workflow_dispatch:
    ```
  - Steps:
    1. Checkout repository.
    2. Run Python ingestion script querying Open-Meteo API for block coordinates.
    3. Trigger `backend/forecast_engine_v2.py` cache warming.
    4. Ping Render health check to verify fresh forecast delivery.

---

### Phase 2: CI/CD Quality Guards & Branch Protection
- [ ] **2.1 Enhance PR CI Pipeline (`.github/workflows/protect-main.yml`):**
  - Add matrix testing across Python 3.11 and 3.12.
  - Run full test suite:
    ```bash
    python -m unittest discover -s tests
    ```
  - Add frontend build validation:
    ```bash
    cd frontend && npm install && npm run build
    ```
  - Block merging if any test fails or frontend fails to compile.
- [x] **2.2 Enforce Git Branching Discipline:**
  - Branch protection on `main`: Reject direct pushes to `main` via `protect-main.yml`.
  - Maintain team member workspace isolation across `frontend/`, `backend/`, `ml/`, and DevOps/root.

---

### Phase 3: Offline Contingency & Docker Packaging
- [ ] **3.1 Multi-Stage Dockerfile & Docker Compose Stack (`docker-compose.yml`):**
  - Create `docker-compose.yml` bundling FastAPI backend, pre-cached model weights, offline Parquet forecast data, and compiled React frontend:
    ```bash
    docker-compose up --build
    ```
  - *Why critical for SIH:* Hackathon convention halls often have overloaded or failing Wi-Fi. Having the full prototype running offline on `localhost:8000` and `localhost:5173` guarantees a flawless demo regardless of connectivity.
- [x] **3.2 Offline Pre-caching Test:**
  - Verify complete disconnected offline operation by querying `/v1/forecast?live=false` across statewide Panchayats.

---

### Phase 4: Disaster Management & Administrative Reporting
- [ ] **4.1 Surface Waterlogging & Flood Risk Calculation:**
  - Implement batch calculation script combining DEM elevation (`elevation_dem_m`), slope, and distance to water bodies (`distance_to_river_m`) with forecast 48h rainfall.
  - Generate a risk table identifying low-lying panchayats vulnerable to water stagnation.
- [ ] **4.2 PMFBY Crop Insurance Loss Verification Export:**
  - Build script to generate PDF / CSV audit reports of verified weather incident triggers (e.g. 3 consecutive days of heat stress during flowering, rainfall > 50 mm) to support crop insurance claims.

---

### Phase 5: Official SIH 6-Slide Presentation Deck & Jury Defense
- [ ] **5.1 Mandatory 6-Slide Deck Preparation (Strict SIH Rules):**
  - **Slide 1 — Title:** PS SIH26074, "From Block to Panchayat: Downscaling Weather Forecasts for Agro-Meteorological Advisory Services", Theme: Disaster Management, Software, Team ID/Name.
  - **Slide 2 — Proposed Solution:** Visual comparison of blurry 25 km block vs. sharp ~2–5 km panchayat forecast; one-line value proposition; key innovations.
  - **Slide 3 — Technical Approach & Results Table:** 5-layer architecture; datasets named (ERA5-Land, IMDAA, CHIRPS, SoilGrids, LGD); Model comparison ladder (M0 Baseline vs M1 vs Hurdle V2 with 99.39% accuracy, 0.56 mm MAE).
  - **Slide 4 — Feasibility & Risk Table:** 3-column table (Risk, Why Real, Mitigation): sparse ground truth, rural digital literacy (voice TTS), connectivity (PWA).
  - **Slide 5 — Impact & Governance Integration:** Plugs into IMD's existing GKMS pipeline; free for farmers; KVK scientist dashboard.
  - **Slide 6 — Research & References:** Citations of IMD publications, SoilGrids, WMO downscaling guidelines, live demo QR codes.
- [ ] **5.2 Jury Question Rehearsals (The 10 Tough Questions):**
  - *Why not just interpolate?* (Interpolation smooths; cannot account for elevation, soil drainage, and local convective cells).
  - *Where is your ground truth?* (AWS stations + high-res IMD gridded satellite estimates).
  - *Why should IMD adopt this?* (Post-processing API layer over existing outputs, zero disruption to existing pipeline).

---

## 5. Cloud Deployment Operations Reference

### Backend Deployment (Render)
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
* **Root Directory:** `.` (uses root `api.py` backward-compatibility shim)
* **Health Check Path:** `/health`

### Frontend Deployment (Vercel)
* **Framework Preset:** Vite
* **Root Directory:** `frontend`
* **Build Command:** `npm run build`
* **Output Directory:** `dist`
* **Rewrites:** Configured in `frontend/vercel.json` for client-side routing.

