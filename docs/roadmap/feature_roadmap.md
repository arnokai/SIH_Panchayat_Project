# TerraMind — Feature Roadmap & 4-Member Action Plan

> **Target:** Smart India Hackathon (SIH 2026 — Problem Statement SIH26074)  
> **Status:** Active development with cloud-deployed prototype (Vercel + Render).  
> **Language:** Strictly English (100% English advisory system, zero regional fonts).  
> **Coverage:** Statewide West Bengal (3,339 Gram Panchayats across 22 Rural Districts).  
> **Default Location:** Amdanga Gram Panchayat (`WB_107778`, LGD `107778`, North 24 Parganas).

---

## ✅ Completed Milestones

- [x] **4-Member Modular Codebase Reorganization:**
  - Separated project into dedicated, conflict-free workspaces: `frontend/`, `backend/`, `rules/`, `ml/`, `data_pipeline/`, `docs/`, and `tests/`.
  - Added root `api.py` backward-compatibility shim guaranteeing uninterrupted Render cloud deployments.
  - Resolved all relative and project-root path imports with fallback support.
  - Verified all integration tests pass 100% cleanly (153/153 tests).
- [x] **Live Cloud Deployments:**
  - Frontend live on Vercel: [sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)
  - Backend live on Render: [sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)
  - Interactive API docs: [sih-panchayat-project.onrender.com/docs](https://sih-panchayat-project.onrender.com/docs)
- [x] **English Advisory Engine (`rules/rules.yaml`):**
  - Integrated 5 core SIH handbook rules (`no_spray_rain`, `heat_stress`, `blast_disease_risk`, `sandy_soil_dry_spell`, `harvest_rain`) + 3 extensions (`moderate_rain`, `light_rain`, `dry_day`).
  - Tested across 5,848 historical weather rows with verified rule triggers.
  - Complete elimination of regional fonts — 100% pure English advisory copy.
- [x] **Frontend Modular Component Architecture:**
  - Decoupled monolithic layout into `src/services/api.js`, `SearchBar.jsx`, `CurrentWeatherHero.jsx`, `QuantileForecastList.jsx`, `AgronomicAlerts.jsx`, `SystemStatsFooter.jsx`, and `utils/formatters.js`.
- [x] **5-Day Quantile Uncertainty Horizon (P10 / P50 / P90):**
  - Visual confidence intervals on daily cards showing minimum dry bound (P10), expected median (P50), and worst-case runoff risk (P90).
- [x] **Operational Agronomic Action Chips:**
  - Direct operational decision pills (`🚫 Do Not Spray`, `✅ Fertilizer Safe`, `🌧️ Check Drainage`, `🌾 Protect Harvest`).
- [x] **Live Dynamic Weather Toggle:**
  - Interactive switcher between dynamic Open-Meteo (ECMWF/GFS) ML downscaling and offline Parquet baseline.
- [x] **Statewide Autocomplete & District Filter:**
  - Debounced search across 3,339 Gram Panchayats with 22-district filter dropdown.
- [x] **Google-Style 24-Hour Hourly Weather Refinement (`HourlyWeatherSlider.jsx`):**
  - Horizontal 24-hour time carousel with daylight markers and weather icons.
  - 3 interactive metric tabs: Elevation-adjusted Temperature (°C), Hurdle Precipitation (%), Wind & Spray Safety.
  - Operational spray window insight banner with DEM lapse rate telemetry pill.
  - Automatic diurnal solar curve fallback guaranteeing zero blank states when offline.

---

## 🌱 Priority 2: Agricultural Intelligence — [Member 2: Backend & Rules]

> 📖 **Full Workspace Guide & Technical Tasks:** See [backend/README.md](../../backend/README.md) or [BACKEND_TODO.md](BACKEND_TODO.md).

- [x] **Pest & Disease Prediction Expansion:**
  - High-humidity streaks (>85% for ≥3 consecutive days) for blast defense, plus Potato Late Blight, Mustard Aphid/Rust, Jute Stem Rot, and Paddy BPH.
- [x] **Actionable Fertilizer & Chemical Spray Windows:**
  - Direct guidance on urea wash-off avoidance, 24-hour spray safety pills, and chemical application timing.
- [x] **Multi-Crop Phenology Support:**
  - Expanded statewide calendar covering Paddy, Potato, Mustard, Jute, and Vegetables.
- [x] **Pydantic v2 Production Schemas:**
  - Strict typing, validation, and auto-generated OpenAPI / Swagger docs on `/docs`.

---

## ⛈️ Priority 3: Machine Learning & Downscaling Refinements — [Member 3: AI / ML & Data]

> 📖 **Full Workspace Guide & Technical Tasks:** See [ml/README.md](../../ml/README.md) or [ML_TODO.md](ML_TODO.md).

- [ ] **1. Ingest Dynamic Atmospheric Physics:**
  - Ingest convective variables (CAPE, Total Column Precipitable Water, 850 hPa wind vectors) to anticipate localized thunderstorm onsets.
- [ ] **2. 3-Stage Hurdle Architecture Enhancement:**
  - Stage 1: Rain Occurrence Classifier
  - Stage 2: Heavy Rain Trigger (>25 mm)
  - Stage 3: Multi-Quantile Regressor (P10, P50, P90 confidence bounds).

---

## 🏛️ Priority 4: Panchayat Administration & DevOps — [Member 4: Manager & DevOps]

> 📖 **Full Workspace Guide & Technical Tasks:** See [docs/architecture/DEVOPS_README.md](../architecture/DEVOPS_README.md) or [DEVOPS_TODO.md](DEVOPS_TODO.md).

- [ ] **Automated Daily Ingestion Scheduler (GitHub Actions / Cron):**
  - Daily cron job at 05:30 IST fetching fresh Open-Meteo feeds and updating the statewide data lake.
- [ ] **Presentation Preparation & Rehearsals:**
  - Align the 6-slide SIH presentation deck highlighting statewide downscaling, P10/P50/P90 uncertainty, and operational farmer actions.

---

## ⏸️ Items Placed On Hold (Backlog & Future Horizon)

| Feature | Status | Rationale / Next Steps |
|---|---|---|
| **Spatial Leaflet Map (`ComparisonMap.jsx`)** | **ON HOLD** | Multi-day spatial downscaling model is undergoing further GIS validation before reactivation. |
| **Offline-First PWA Mode** | **ON HOLD** | Platform is 100% focused on real-time online dynamic forecasts. Service worker caching staged for subsequent phase. |
| **Automatic GPS Geolocation & LocalStorage** | **ON HOLD (TODO)** | Default is set to Amdanga (`WB_107778`). Location auto-discovery will be added later. |
| **Voice Audio (TTS) & WhatsApp Sharing** | **ON HOLD (Phase 4)** | Multichannel voice synthesis and WhatsApp community bulletins are planned for Phase 4 field expansion. |
