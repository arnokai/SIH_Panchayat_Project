# TerraMind DevOps, Architecture & Project Management Guide

> **Assigned Owner:** Member 4 — Project Manager & DevOps  
> **Workspaces:** Root, `.github/`, `docs/`, `tests/`  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Live Deployments:**
> - 🌐 Frontend: [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)
> - ⚡ Backend: [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)
> - 📚 Swagger Docs: [https://sih-panchayat-project.onrender.com/docs](https://sih-panchayat-project.onrender.com/docs)
> **Status:** Pure Parquet lake complete (2.44M rows, 22 districts). Two-Stage Hurdle models operational (`degraded: false`). Dynamic weather API integration active. Production CLI `terramind-engine` available. All 248 unit tests passing (100% green).

---

## 1. Executive Summary & Role Mission

As the **Project Manager & DevOps Engineer (Member 4)**, you ensure uninterrupted system uptime, automated CI/CD validation, zero-friction developer coordination across the team roles, disaster recovery, and hackathon presentation delivery:
1. **Cloud Deployments & Infrastructure:** Managing production hosting on Vercel and Render with auto-deployment triggers, zero downtime, and health checks (`/health` returning `degraded: false`).
2. **Automated CI/CD Quality Guards (`.github/workflows/`):** Enforcing automated test execution and preventing unauthorized direct pushes to `main`.
3. **Automated Data Lake QA Engine:** Maintaining statewide partitioned data lake validation and zero data leakage.
4. **Cadastral Boundary Precision:** Enforcing 100% zero-displacement spatial grounding (all 3,339 Gram Panchayats strictly inside their containing Survey of India block envelopes).
5. **Multi-Channel & Disaster Ops:** Verifying PMFBY cryptographic insurance certificate issuance, Bay of Bengal cyclone alerting, SMS generation ($\le 160$ chars), and 1800-TERRAMIND IVR hotline scripts.
6. **SIH Compliance & Presentation Management:** Managing the official 6-slide presentation deck, risk mitigation tables, and jury defense strategy.

---

## 2. Completed Engineering Milestones

- [x] **Pure Parquet Statewide Data Lake Migration:**
  - Eradicated all active CSV dependencies from data processing pipelines.
  - Partitioned 2,440,809 records into 22 district Hive partitions (`data_pipeline/processed/statewide/district_name=*/data.parquet`).
  - Verified 3,339 unique Gram Panchayats over 731 continuous days (`2024-01-01` to `2025-12-31`) with zero duplicate keys and zero NaNs.
- [x] **Automated Data Lake QA Engine:**
  - Developed `data_pipeline/storage/qa_validator.py` and published `data_pipeline/reports/statewide_qa_report.md` confirming 100% integrity pass.
- [x] **248-Test Automated Verification Suite:**
  - Expanded test coverage across 23 test files in `tests/` validating registry boundaries, cadastral precision, geospatial features, physical realism, pipeline leakage, forecast engine, regional models, insurance, phenology, and advisory rules in under 20 seconds.
- [x] **Two-Stage Hurdle Model Deployment:**
  - Trained and integrated `ml/models/statewide_hurdle_v2.pkl` (99.39% accuracy, 0.9999 ROC-AUC, MAE 0.56 mm) alongside 3 specialized regional models (`hurdle_delta.pkl`, `hurdle_laterite.pkl`, `hurdle_terai.pkl`), delivering $P_{10}$, $P_{50}$, and $P_{90}$ precipitation bounds and clearing `degraded: false`.
- [x] **Cadastral Boundary Precision (100% Zero Displacement):**
  - Bound all 3,339 Gram Panchayats strictly inside containing Survey of India Community Development Block polygons.
  - Implemented sub-millisecond in-memory caching (`_init_statewide_boundaries_cache`) in FastAPI.
- [x] **Dedicated Production CLI (`terramind-engine`):**
  - Packaged unified CLI entrypoint for serving, cache management, and data lake verification.
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
│       └── daily-weather-sync.yml   # Daily 05:30 IST weather ingestion cron
├── docs/
│   ├── team_roles.md                # 4-member workspace division and git branch rules
│   ├── model_card.md                # Scientific model documentation & metrics
│   ├── data_contract.md             # Pure Parquet data lake schema & handoff contracts
│   ├── statewide_requirements.md    # Statewide acceptance criteria & verification log
│   └── DEVOPS_README.md             # (This DevOps guide & roadmap)
├── tests/                           # 248-test automated verification suite (23 test files)
│   ├── test_statewide_pipeline.py   # 67 statewide Parquet lake tests
│   ├── test_statewide_registry.py   # Geographic boundary & LGD tests
│   ├── test_statewide_geo_features.py # DEM, SoilGrids, river proximity tests
│   ├── test_forecast_engine_v2.py   # 5-day coordinator, live API caching, offline fallback
│   ├── test_regional_models.py      # Delta, Laterite, and Terai regional hurdle tests
│   ├── test_insurance_and_phenology.py # PMFBY certificates & GDD phenology tests
│   ├── test_cyclone_tracker.py      # Bay of Bengal cyclone engine tests
│   ├── test_ai_chat_engine.py       # Dual AI chatbot copilot tests
│   └── ...                          # Challenger & integration test suites
├── Dockerfile                       # Multi-stage production container (Python 3.12-slim)
├── requirements.txt                 # Backend & ML Python dependencies
├── vercel.json                      # Vercel SPA routing rules
└── docs/roadmap/DEVOPS_TODO.md       # DevOps action checklist
```

---

## 4. Verification & Testing Reference

```bash
# Run complete 248-test verification suite
.venv/bin/pytest tests/ -k "not test_05_live_weather_service"

# Start backend using production CLI
.venv/bin/terramind-engine serve --host 0.0.0.0 --port 8000 --reload

# Build frontend production bundle
pnpm --dir frontend build
```

---

## 5. Official SIH 6-Slide Presentation Deck & Jury Defense

### Mandatory 6-Slide Deck Preparation (Strict SIH Guidelines)
1. **Slide 1 — Title & Problem Statement:**
   - **Problem ID:** SIH26074 (Ministry of Earth Sciences)
   - **Title:** "From Block to Panchayat: Downscaling Weather Forecasts for Agro-Meteorological Advisory Services"
   - **Theme:** Disaster Management / Agriculture
   - **Core Pitch:** Transforming blurry ~25 km block forecasts into sharp ~2 km Gram Panchayat precision across all 3,339 rural West Bengal Panchayats.
2. **Slide 2 — Proposed Solution & Innovations:**
   - Two-Stage Hurdle ML downscaling ($P_{10}/P_{50}/P_{90}$ quantile bounds).
   - High-precision block-bounded cadastral maps (Survey of India envelopes).
   - Parametric PMFBY crop insurance certificate generation with cryptographic HMAC-SHA256 signatures.
   - Live Bay of Bengal cyclone tracking with IMD RSMC alert signals.
   - Comprehensive Crop Command Center (Pest Doctor, POP, NPK calculator, FAO-56 $ET_c$).
3. **Slide 3 — Technical Architecture & Quantitative Results:**
   - 5-layer pipeline: Ingestion → Pure Parquet Lake → Regional Hurdle Models → Dynamic Phenology → Multi-Channel Delivery.
   - Proven Accuracy: 99.39% rain occurrence classification, 0.56 mm MAE, 100% quantile monotonicity.
   - 248 / 248 automated tests passing green.
4. **Slide 4 — Feasibility, Risk Mitigation & Zero-Displacement GIS:**
   - Challenge: Sparse ground station density in rural areas.
   - Mitigation: Blending Copernicus 30m DEM elevation, SoilGrids edaphic properties, and satellite reanalysis.
   - 100% Zero-Displacement: All 3,339 GP polygons strictly bounded inside their parent block.
5. **Slide 5 — Impact, Governance & Multi-Channel Reach:**
   - Seamless integration with IMD Gramin Krishi Mausam Sewa (GKMS) pipeline.
   - Multi-channel delivery: Web dashboard, $\le 160$-char SMS alerts, 1800-TERRAMIND IVR hotline, and printable A4 Krishi Bulletins for CSC notice boards.
6. **Slide 6 — Live Demo & Scientific References:**
   - Live Web Application: `https://sih-panchayat-project.vercel.app`
   - Live Backend API: `https://sih-panchayat-project.onrender.com`
   - References: IMD agromet bulletins, FAO-56 Irrigation guidelines, Copernicus 30m DEM, SoilGrids 250m.

---

## 6. Cloud Deployment Operations Reference

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
