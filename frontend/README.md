# TerraMind Frontend Workspace & Operational Guide

> **Assigned Owner:** Member 1 — Frontend Engineer  
> **Workspace:** `frontend/`  
> **Framework:** React 19 (`^19.2.8`) + Vite 8 (`^8.2.2`)  
> **Live Deployment (Vercel):** [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)  
> **Backend API (Render):** [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Coverage:** Statewide West Bengal — 3,339 Gram Panchayats across 22 Rural Districts (100% Equal Presentation)  
> **Language:** Strictly English (100% English advisory system, zero regional fonts)  
> **Default Location:** Amdanga Gram Panchayat (`WB_107778`, LGD `107778`, North 24 Parganas)  
> **Status:** Production-ready operational architecture. Statewide autocomplete search, 22-district filtering, 5-day quantile uncertainty horizon (P10/P50/P90), active Leaflet cadastral map with Survey of India block envelopes, Copernicus 30m Micro-Terrain HUD, Bay of Bengal cyclone tracker, crop advisory command center, PMFBY parametric insurance claim generator, and dual AI chatbot widget active.

---

## 1. Executive Summary & Architecture

The **TerraMind Frontend** provides rural farmers, Gram Panchayat agricultural officers (*Krishi Sahayaks*), and district planners with an ultra-accessible, high-contrast agro-meteorological dashboard. It transforms complex two-stage machine learning downscaling predictions and live atmospheric forecasts into actionable farming decisions.

### Core Implemented Capabilities:

1. **Statewide 3,339 Gram Panchayat Autocomplete & District Filter:**
   - Clean 3-element search bar across all 22 rural districts of West Bengal, querying `/v1/statewide/panchayats` to instantly locate and inspect any Gram Panchayat.
   - **100% Equal Representation:** All 3,339 Gram Panchayats are first-class equals (specialized pilot tiers eliminated).
2. **1-Click Browser GPS Auto-Detect & LocalStorage Memory:**
   - Instant geolocation using device GPS coordinates resolved via vectorized Haversine lookup (`/v1/statewide/nearest`) in <15ms.
   - Persists user preferences (selected Gram Panchayat, active crop) across browser sessions.
3. **Current Weather Hero & Telemetry:**
   - Displays real-time temperature, daily high/low, rain probability, surface humidity, and 10m wind speed with inline vector SVG condition icons (`WeatherIcon.jsx`).
   - Live/Offline toggle lets users compare real-time ECMWF/GFS dynamic downscaling against the offline Parquet baseline.
4. **Multi-Day 24-Hour Hourly Weather & Spray Slider (`HourlyWeatherSlider.jsx`):**
   - 24-hour hour-by-hour forecast dynamically synchronized across all 5 forecast days (Today, Tomorrow, Day +2, Day +3, Day +4).
   - Interactive day picker tabs embedded directly in the card header.
   - 3 interactive metric views: Elevation-adjusted Temperature (°C), Precipitation Chance (%) & mm, Wind & Spray Safety.
   - Dynamic Operational Farm Work Advice banner auto-synthesizing the optimal daytime spraying window.
5. **5-Day Quantile Uncertainty Horizon (P10 / P50 / P90):**
   - Visual confidence spread bars showing the lower dry bound (P10), expected median (P50), and worst-case runoff bound (P90).
   - Operational agronomic action chips on daily cards (e.g. `🚫 Do Not Spray`, `✅ Fertilizer Safe`, `🌧️ Check Drainage`, `🌾 Protect Harvest`).
6. **Active Operational Cadastral Map (`ComparisonMap.jsx`):**
   - High-precision block-bounded parcel map: all 3,339 Gram Panchayats are topologically constrained within authentic Survey of India Community Development Block polygons (`#0f172a`, dashed).
   - Contiguous Voronoi parcel partitions with emerald active GP highlighting.
   - Interactive polygon clicks to seamlessly inspect neighboring Gram Panchayats.
   - Live Doppler radar overlay with RainViewer API integration and animated frame controls (`RadarControls.jsx`).
7. **Copernicus 30m Micro-Terrain Topo HUD (`MicroTerrainHud.jsx`):**
   - Displays physical orographic telemetry derived from European Space Agency (ESA) Copernicus 30m DEM: absolute elevation (m), terrain slope (°), aspect orientation, relative height, and river proximity (m).
8. **Bay of Bengal Live Cyclone Tracker (`CycloneTracker.jsx`):**
   - Live tropical storm tracking across the North Bay of Bengal basin.
   - Displays IMD RSMC alert levels (Green / Yellow / Orange / Red), system classifications, maximum sustained wind speeds, and port warning signals (e.g. Local Cautionary Signal No. 3).
9. **Crop Advisory Command Center (`CropAdvisoryCommand.jsx`, `PestDiseaseDoctor.jsx`):**
   - Comprehensive agricultural operations suite covering 6 major crops (Paddy, Potato, Mustard, Jute, Maize, Vegetables).
   - Package of Practices (POP) with season-specific agronomic guidelines.
   - NPK Fertilizer Calculator recommending urea, DAP, and MOP dosages based on soil texture.
   - FAO-56 $ET_c$ Crop Water Balance calculator estimating daily evapotranspiration and irrigation requirement.
   - Pest & Disease Doctor diagnostic assistant identifying high-risk fungal/bacterial vectors.
10. **PMFBY Parametric Insurance Claim Generator (`InsuranceClaimModal.jsx`):**
    - Evaluates weather triggers (excess rainfall, heat stress, prolonged dry spells).
    - Generates cryptographically signed (HMAC-SHA256) claim verification certificates with QR payloads for seamless insurance claim settlement.
11. **Dual AI Agro-Climatic Chatbot Widget (`AiChatWidget.jsx`):**
    - Floating interactive conversational copilot grounded in real-time downscaled weather forecasts and agricultural rule engine logic (`POST /v1/ai/chat`).
12. **Multi-Channel Dissemination Systems:**
    - $\le 160$-Character SMS Alert Generator for regional telecommunications delivery.
    - 1800-TERRAMIND IVR Voice Hotline script simulator.
    - Web Speech API browser voice synthesis for rural farmers.
    - Printable A4 Krishi Bulletin (`PrintableBulletin.jsx`) formatted for Common Service Center (CSC) and Panchayat notice boards.
13. **Trust & Transparency Panel (`TrustTransparencyPanel.jsx`):**
    - Transparently reveals ML model lineage, training datasets, feature weights, and uncertainty metrics to reinforce user trust.
14. **Zero Broken Assets:**
    - Self-contained vector SVG icons (`WeatherIcon.jsx`) ensuring reliable offline and online rendering without external CDN dependencies.
15. **Platform Telemetry Footer (`SystemStatsFooter.jsx`):**
    - Live indicators verifying the 2.44M row statewide data lake, 3,339 GPs, 22 districts, and QA validation status.

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
│   ├── App.jsx                     # Modular root layout coordinator
│   ├── App.css                     # High-contrast component-scoped stylesheet
│   ├── services/
│   │   └── api.js                  # Centralized API service (fetchForecast, boundaries, chat, etc.)
│   ├── components/
│   │   ├── SearchBar.jsx           # 3-element search bar + 3,339 GP search + district filter + GPS auto-detect
│   │   ├── CurrentWeatherHero.jsx  # Hero weather card, live/offline toggle, crop pills, surface metrics
│   │   ├── HourlyWeatherSlider.jsx # 24-hour weather & spray slider (multi-day synchronized)
│   │   ├── QuantileForecastList.jsx# 5-day horizon cards with P10/P50/P90 uncertainty bars
│   │   ├── AgronomicAlerts.jsx     # Prioritized agricultural advisory cards
│   │   ├── ComparisonMap.jsx       # Active Leaflet cadastral map with Survey of India block envelopes
│   │   ├── MicroTerrainHud.jsx     # Copernicus 30m elevation, slope, aspect, and river distance HUD
│   │   ├── CycloneTracker.jsx      # Bay of Bengal tropical storm tracking & port warning alert panel
│   │   ├── CropAdvisoryCommand.jsx # Comprehensive Crop Command: POP, NPK calculator, FAO-56 ETc
│   │   ├── PestDiseaseDoctor.jsx   # Pest & disease diagnostic assistant
│   │   ├── InsuranceClaimModal.jsx # PMFBY parametric insurance claim generator & HMAC certificate
│   │   ├── AiChatWidget.jsx        # Floating AI Agro-Climatic Chatbot copilot
│   │   ├── PrintableBulletin.jsx   # Printable A4 Krishi Bulletin for CSC notice boards
│   │   ├── TrustTransparencyPanel.jsx # Model lineage, feature importances, and trust metrics
│   │   ├── RadarControls.jsx       # RainViewer Doppler radar animation controls
│   │   ├── WeatherIcon.jsx         # Pure vector SVG weather icons (zero broken images / 100% offline)
│   │   └── SystemStatsFooter.jsx   # Data lake telemetry footer (2.44M rows, 3,339 GPs)
│   ├── utils/
│   │   └── formatters.js           # Date formatting and operational action chip heuristics
│   └── index.css                   # Global base resets and typography
└── README.md                       # Frontend technical documentation
```

---

## 3. Local Development & Deployment

### Prerequisites
- Node.js >= 18.0.0 (Node 20+ recommended)
- pnpm >= 9.0.0 or npm >= 9.0.0

### Run Commands

```bash
# 1. Navigate to frontend workspace
cd frontend

# 2. Install dependencies
pnpm install # or npm install

# 3. Start local development server (http://localhost:5173)
pnpm dev # or npm run dev

# 4. Build for production (outputs to frontend/dist in ~220ms)
pnpm build # or npm run build

# 5. Run ESLint code checks (must pass with 0 errors)
pnpm lint # or npm run lint

# 6. Preview production build locally
pnpm preview # or npm run preview
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
| `/v1/forecast` | `GET` | `panchayat_id`, `days=5`, `lang=en`, `crop`, `live` | Retrieves 5-day downscaled rainfall (P10/P50/P90), temperatures, advisories, and live dynamic weather telemetry. |
| `/v1/statewide/panchayats` | `GET` | `search`, `district`, `limit=8` | Real-time debounced autocomplete search across all 3,339 Gram Panchayats in West Bengal. |
| `/v1/statewide/districts` | `GET` | — | Populates the 22-district filter dropdown in the search header. |
| `/v1/statewide/stats` | `GET` | — | Footer telemetry counter (2.44M rows, 3,339 Panchayats, 22 Districts). |
| `/v1/statewide/boundaries` | `GET` | `block_name`, `panchayat_id` | Renders high-precision block-bounded GeoJSON cadastral polygons on the Leaflet map. |
| `/v1/ai/chat` | `POST` | `{"query": str, "panchayat_id": str, "crop": str}` | Drives the interactive AI Agro-Climatic Chatbot widget. |
| `/v1/cyclone/active` | `GET` | — | Fetches real-time Bay of Bengal cyclone telemetry and port warnings. |
| `/v1/insurance/certificate` | `POST` | `{"panchayat_id": str, "crop": str, "trigger_type": str}` | Issues HMAC-SHA256 cryptographically signed PMFBY insurance claim certificates. |
| `/v1/radar/timestamps` | `GET` | — | Provides timestamped radar scan frames for animated Doppler rain overlays. |
| `/v1/agromet/bulletin` | `GET` | `district` | Retrieves official IMD district agromet bulletins. |

---

## 5. UI Workflows

1. **Statewide Search & Selection:**
   - Farmer or official searches for a Gram Panchayat (e.g., "Amdanga", "Banchukamari", "Falakata") or filters by district.
   - Selecting a GP loads its 5-day Hurdle AI forecast, centers the Leaflet cadastral map, and renders an active breadcrumb card showing LGD code, elevation (m), and soil texture.
2. **Hero Weather Telemetry:**
   - Visual card displays real-time temperature, condition icon, rainfall expectation, and surface wind/humidity.
   - Live/Offline toggle lets users compare real-time ECMWF/GFS dynamic downscaling against the offline Parquet baseline.
   - Crop pills toggle between Paddy, Potato, Mustard, Jute, Maize, and Vegetables with instant advisory recalculation.
3. **Hourly Weather & Spray Planning:**
   - Interactive 24-hour timeline synchronized across all 5 forecast days.
   - Dynamically highlights safe morning spraying windows based on humidity, temperature, and wind speed.
4. **Cadastral Map Navigation:**
   - Shows the active Gram Panchayat highlighted in emerald within its containing Survey of India block boundary.
   - Clicking neighboring parcels seamlessly switches the active forecast context.
   - Toggleable RainViewer Doppler radar overlay visualizes real-time rain clouds.
5. **Crop Advisory Command Center & Pest Doctor:**
   - Farmers access specific Package of Practices (POP), compute exact NPK fertilizer requirements, and run pest diagnostics for early disease intervention.
6. **Emergency & Disaster Operations:**
   - In case of severe weather, the Cyclone Tracker alerts users with official port warning signals.
   - Impacted farmers can instantly generate a cryptographically verifiable PMFBY insurance claim certificate.
