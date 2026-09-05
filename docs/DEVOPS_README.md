# TerraMind DevOps, Architecture & Project Management Guide

> **Assigned Owner:** Member 4 — Project Manager & DevOps  
> **Workspaces:** Root, `.github/`, `docs/`, `tests/`  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Live Deployments:**
> - 🌐 Frontend: [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)
> - ⚡ Backend: [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)
> - 📚 Swagger Docs: [https://sih-panchayat-project.onrender.com/docs](https://sih-panchayat-project.onrender.com/docs)
> **Status:** CI guards active. Live cloud hosting operational. Offline demo contingency and automated cron scheduler in progress.

---

## 1. Executive Summary & Role Mission

As the **Project Manager & DevOps Engineer (Member 4)**, you are the backbone of the team. You are responsible for ensuring uninterrupted system uptime, automated CI/CD validation, zero-friction developer coordination across the other 3 roles, disaster recovery, and hackathon presentation delivery:
1. **Cloud Deployments & Infrastructure:** Managing production hosting on Vercel and Render with auto-deployment triggers, zero downtime, and health checks.
2. **Automated CI/CD Quality Guards (`.github/workflows/`):** Enforcing automated test execution and preventing broken code from merging into `main`.
3. **Automated Data Ingestion Schedulers:** Configuring automated cron jobs (daily 05:30 IST) to ingest fresh weather data and trigger pre-cached panchayat advisories.
4. **Offline Demo Contingency (Docker):** Building a self-contained, 1-command Docker container so the entire application can run offline during judging if venue Wi-Fi fails.
5. **SIH Compliance & Presentation Management:** Managing the official 6-slide presentation deck, risk mitigation tables, and jury defense strategy.

---

## 2. Directory Layout & Workspace Ownership

```text
.
├── .github/
│   └── workflows/
│       ├── protect-main.yml         # CI workflow: runs tests on PRs to main
│       └── daily-weather-sync.yml   # (In Development) Daily 05:30 IST weather ingestion cron
├── docs/
│   ├── team_roles.md                # 4-member workspace division and git branch rules
│   ├── model_card.md                # Scientific model documentation & metrics
│   └── DEVOPS_README.md             # (This DevOps guide & roadmap)
├── tests/
│   ├── test_advisory_context.py     # Advisory context creation tests
│   ├── test_advisory_rules.py       # Rule evaluation against 5,848 historical weather rows
│   ├── test_forecast_advisories.py  # Forecast-to-advisory integration tests
│   └── test_api_endpoints.py        # (In Development) FastAPI TestClient integration suite
├── Dockerfile                       # Multi-stage production container
├── docker-compose.yml               # Local offline stack (Backend + Frontend)
├── requirements.txt                 # Backend & ML Python dependencies
├── vercel.json                      # Vercel SPA routing rules
└── DEVOPS_TODO.md                   # Root-level DevOps action checklist
```

---

## 3. Action Plan & Task Checklist

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
    2. Run Python ingestion script querying Open-Meteo API for Amdanga Block coordinates.
    3. Trigger `backend/services/weather_service.py` cache update.
    4. Ping Render health check to verify fresh forecast delivery.

---

### Phase 2: CI/CD Quality Guards & Branch Protection
- [ ] **2.1 Enhance PR CI Pipeline (`.github/workflows/protect-main.yml`):**
  - Add matrix testing across Python 3.11 and 3.12.
  - Run full test suite:
    ```bash
    python -m unittest discover tests/
    ```
  - Add frontend build validation:
    ```bash
    cd frontend && npm install && npm run build
    ```
  - Block merging if any test fails or frontend fails to compile.
- [ ] **2.2 Enforce Git Branching Discipline:**
  - Branch protection on `main`: Require pull request reviews before merging.
  - Ensure team members only commit within their assigned folders:
    - Member 1: `frontend/`
    - Member 2: `backend/` and `rules/`
    - Member 3: `ml/` and `data_pipeline/`
    - Member 4: `docs/`, `.github/`, `tests/`, root

---

### Phase 3: Offline Contingency & Docker Packaging
- [ ] **3.1 Multi-Stage Dockerfile & Docker Compose:**
  - Build self-contained image packaging FastAPI backend, compiled React frontend, pre-cached model weights, and offline forecast data:
    ```bash
    docker-compose up --build
    ```
  - *Why critical for SIH:* Hackathon convention halls often have overloaded or failing Wi-Fi. Having the full prototype running offline on `localhost:8000` and `localhost:5173` guarantees a flawless demo regardless of connectivity.
- [ ] **3.2 Offline Pre-caching Test:**
  - Verify complete disconnected offline operation by disconnecting Wi-Fi and clicking through all 8 panchayats.

---

### Phase 4: Disaster Management & Administrative Reporting
- [ ] **4.1 Surface Waterlogging & Flood Risk Calculation:**
  - Implement batch calculation script combining DEM elevation (`elevation_dem_m`), slope, and distance to water bodies (`distance_to_river_m`) with forecast 48h rainfall.
  - Generate a risk table identifying low-lying panchayats (e.g. Maricha, Chandigarh) vulnerable to water stagnation.
- [ ] **4.2 PMFBY Crop Insurance Loss Verification Export:**
  - Build script to generate PDF / CSV audit reports of verified weather incident triggers (e.g. 3 consecutive days of heat stress during flowering, rainfall > 50 mm) to support crop insurance claims.

---

### Phase 5: Official SIH 6-Slide Presentation Deck & Jury Defense
- [ ] **5.1 Mandatory 6-Slide Deck Preparation (Strict SIH Rules):**
  - **Slide 1 — Title:** PS SIH26074, "From Block to Panchayat: Downscaling Weather Forecasts for Agro-Meteorological Advisory Services", Theme: Disaster Management, Software, Team ID/Name.
  - **Slide 2 — Proposed Solution:** Visual comparison of blurry 25 km block vs. sharp ~2–5 km panchayat forecast; one-line value proposition; key innovations.
  - **Slide 3 — Technical Approach & Results Table:** 5-layer architecture; datasets named (ERA5-Land, IMDAA, CHIRPS, SoilGrids, LGD); Model comparison ladder (M0 Baseline vs M1 vs M3 vs M4 Tweedie/Quantile).
  - **Slide 4 — Feasibility & Risk Table:** 3-column table (Risk, Why Real, Mitigation): sparse ground truth, rural digital literacy (voice TTS), connectivity (PWA).
  - **Slide 5 — Impact & Governance Integration:** Plugs into IMD's existing GKMS pipeline; free for farmers; KVK scientist dashboard.
  - **Slide 6 — Research & References:** Citations of IMD publications, SoilGrids, WMO downscaling guidelines, live demo QR codes.
- [ ] **5.2 Jury Question Rehearsals (The 10 Tough Questions):**
  - *Why not just interpolate?* (Interpolation smooths; cannot account for elevation, soil drainage, and local convective cells).
  - *Where is your ground truth?* (AWS stations + high-res IMD gridded satellite estimates).
  - *Why should IMD adopt this?* (Post-processing API layer over existing outputs, zero disruption to existing pipeline).

---

## 4. Cloud Deployment Operations Reference

### Backend Deployment (Render)
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `uvicorn api:app --host 0.0.0.0 --port `
* **Root Directory:** `.` (uses root `api.py` backward-compatibility shim)
* **Health Check Path:** `/health`

### Frontend Deployment (Vercel)
* **Framework Preset:** Vite
* **Root Directory:** `frontend`
* **Build Command:** `npm run build`
* **Output Directory:** `dist`
* **Rewrites:** Configured in `frontend/vercel.json` for client-side routing.
