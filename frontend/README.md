# TerraMind Frontend Workspace & Operational Guide

> **Assigned Owner:** Member 1 — Frontend Engineer  
> **Workspace:** `frontend/`  
> **Framework:** React 19 (`^19.2.8`) + Vite 8 (`^8.2.2`)  
> **Live Deployment (Vercel):** [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)  
> **Backend API (Render):** [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Coverage:** Statewide West Bengal — 3,339 Gram Panchayats across 22 Rural Districts  
> **Language:** Strictly English (100% English advisory system, zero regional fonts)  
> **Default Location:** Amdanga Gram Panchayat (`WB_107778`, LGD `107778`, North 24 Parganas)  
> **Status:** Production-ready modular architecture. Statewide autocomplete search, 22-district filtering, 5-day quantile uncertainty horizon (P10/P50/P90), agronomic action badges, and live dynamic Open-Meteo downscaling active.

---

## 1. Executive Summary & Architecture

The **TerraMind Frontend** provides rural farmers, Gram Panchayat agricultural officers (*Krishi Sahayaks*), and district planners with an ultra-accessible, high-contrast agro-meteorological dashboard. It transforms complex two-stage machine learning downscaling predictions and live atmospheric forecasts into actionable farming decisions.

### Core Implemented Capabilities:
1. **Statewide 3,339 Gram Panchayat Autocomplete & District Filter:** Real-time debounced search across all 22 rural districts of West Bengal, querying `/v1/statewide/panchayats` to instantly locate and inspect any Gram Panchayat with verified Local Government Directory (LGD) codes, elevation, and soil texture.
2. **Current Weather Hero & Telemetry:** Displays current temperature, daily high/low, rain probability, surface humidity, and 10m wind speed with dynamic weather condition icons.
3. **Live / Offline Model Switcher:** Real-time toggle between live dynamic Open-Meteo ECMWF/GFS meteorological ingestion downscaled by the Hurdle ML model and the offline Parquet baseline.
4. **Crop Switcher:** Instant toggle between **Paddy** and **Vegetables** triggering dynamic advisory heuristic recalculation.
5. **5-Day Quantile Uncertainty Horizon (P10 / P50 / P90):** Visual confidence spread bars showing the lower dry bound (P10), expected median (P50), and worst-case runoff bound (P90).
6. **Operational Agronomic Action Chips:** High-contrast decision pills directly on daily cards (e.g. `🚫 Do Not Spray`, `✅ Fertilizer Safe`, `🌧️ Check Drainage`, `🌾 Protect Harvest`).
7. **Ranked Agricultural Advisories:** Prioritized advisory cards (High Alert, Caution Warning, Favorable Window) with actionable plain English guidance.
8. **Platform Telemetry Footer:** Live indicators verifying the 2.44M row statewide data lake, 3,339 GPs, 22 districts, and QA validation status.

### On Hold / Roadmap Items:
* **Spatial Comparison Map (`ComparisonMap.jsx`):** On hold for future GIS spatial model refinement.
* **Offline Mode / PWA:** On hold (system is 100% real-time and online dynamic).
* **Automatic Geolocation / GPS:** On hold (tracked in TODO roadmap).
* **Google-Style Hourly Weather Refinement:** Next major feature in active planning (24-hour horizontal slider with Temperature, Precipitation %, and Wind/Spray Safety tabs refined by Hurdle ML).
* **Multichannel Dissemination (Voice TTS & WhatsApp):** Staged for Phase 4 deployment.

---

## 2. Directory Structure & Key Files

```text
frontend/
├── index.html                      # HTML entry point and viewport configuration
├── package.json                    # Dependencies: React 19.2, Leaflet 1.9, React-Leaflet 5, Vite 8
├── vite.config.js                  # Vite 8 bundler configuration with React plugin
├── vercel.json                     # Vercel SPA client-side rewrite rules
├── eslint.config.js                # ESLint flat configuration (zero errors, zero warnings)
├── .env                            # API base URL configuration (VITE_API_BASE_URL)
├── public/
│   ├── favicon.svg                 # TerraMind browser favicon
│   └── icons.svg                   # Vector icon definitions
├── src/
│   ├── main.jsx                    # React root entry point (StrictMode mount)
│   ├── App.jsx                     # Modular root layout coordinator (~160 lines)
│   ├── App.css                     # High-contrast component-scoped stylesheet
│   ├── services/
│   │   └── api.js                  # Centralized API service (fetchForecast, search, districts, stats)
│   ├── components/
│   │   ├── SearchBar.jsx           # Debounced 3,339 GP search + 22-district filter + breadcrumbs
│   │   ├── CurrentWeatherHero.jsx  # Hero weather card, live/offline toggle, crop pills, surface metrics
│   │   ├── HourlyWeatherSlider.jsx # 24-hour Google-style weather & spray window slider (3 tabs)
│   │   ├── QuantileForecastList.jsx# 5-day horizon cards with P10/P50/P90 uncertainty bars
│   │   ├── AgronomicAlerts.jsx     # Prioritized agricultural advisory cards
│   │   └── SystemStatsFooter.jsx   # Data lake telemetry footer (2.44M rows, 3,339 GPs)
│   ├── utils/
│   │   └── formatters.js           # Date formatting and operational action chip heuristics
│   ├── ComparisonMap.jsx           # [ON HOLD] Spatial map component
│   └── index.css                   # Global base resets and typography
└── README.md                       # Frontend technical documentation
```

---

## 3. Local Development & Deployment

### Prerequisites
- Node.js >= 18.0.0 (Node 20+ recommended)
- npm >= 9.0.0

### Run Commands

```bash
# 1. Navigate to frontend workspace
cd frontend

# 2. Install dependencies
npm install

# 3. Start local development server (http://localhost:5173)
npm run dev

# 4. Build for production (outputs to frontend/dist in ~200ms)
npm run build

# 5. Run ESLint code checks (must pass with 0 errors)
npm run lint

# 6. Preview production build locally
npm run preview
```

### Environment Configuration (`.env`)

```env
# Local development backend:
# VITE_API_BASE_URL=http://127.0.0.1:8000

# Production Render cloud backend (Active Default):
VITE_API_BASE_URL=https://sih-panchayat-project.onrender.com
```

If `VITE_API_BASE_URL` is omitted, the frontend automatically defaults to `http://127.0.0.1:8000`.

---

## 4. API Endpoints Consumed

| Endpoint | Method | Parameters | Usage in Frontend |
| :--- | :--- | :--- | :--- |
| `/v1/forecast` | `GET` | `panchayat_id`, `days=5`, `lang=en`, `crop`, `live` | Retrieves 5-day downscaled rainfall (P10/P50/P90), temperatures, advisories, and live dynamic weather telemetry (`is_live_dynamic`, `live_weather`). |
| `/v1/statewide/panchayats` | `GET` | `search`, `district`, `limit=8` | Real-time debounced autocomplete search across all 3,339 Gram Panchayats in West Bengal. |
| `/v1/statewide/districts` | `GET` | — | Populates the 22-district filter dropdown in the search header. |
| `/v1/statewide/stats` | `GET` | — | Footer telemetry counter (2.44M rows, 3,339 Panchayats, 22 Districts). |

---

## 5. UI Workflows

1. **Statewide Search & Selection:**
   - Farmer or official searches for a Gram Panchayat (e.g., "Amdanga", "Banchukamari", "Falakata") or filters by district.
   - Selecting a GP loads its 5-day Hurdle AI forecast and renders an active breadcrumb card showing LGD code, elevation (m), and soil texture.
2. **Hero Weather Telemetry:**
   - Visual card displays real-time temperature, condition icon, rainfall expectation, and surface wind/humidity.
   - Live/Offline toggle lets users compare real-time ECMWF/GFS dynamic downscaling against the offline Parquet baseline.
   - Crop pills toggle between Paddy and Vegetables with instant advisory recalculation.
3. **5-Day Uncertainty Spread (P10 / P50 / P90):**
   - Each card visualizes the Hurdle ML model's confidence interval.
   - Action chips provide instant operational instructions (e.g. *Safe to Spray*, *Fertilizer Safe*).
4. **Active Roadmaps (Next Steps):**
   - Google-style hourly weather slider with Hurdle ML refinement.
   - Spatial map re-activation following GIS model validation.
