# TerraMind Frontend Workspace & Operational Guide

> **Assigned Owner:** Member 1 — Frontend Engineer  
> **Workspace:** `frontend/`  
> **Framework:** React 19 (`^19.2.8`) + Vite 8 (`^8.2.2`) + React-Leaflet 5 (`^5.0.0`)  
> **Live Deployment (Vercel):** [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)  
> **Backend API (Render):** [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Coverage:** Statewide West Bengal — 3,339 Gram Panchayats across 22 Rural Districts  
> **Status:** Live in production on Vercel. Statewide autocomplete search, district selection, interactive spatial comparison map, and live dynamic Open-Meteo downscaling badge operational.

---

## 1. Executive Summary & Architecture

The **TerraMind Frontend** provides rural farmers, Gram Panchayat agricultural officers (*Krishi Sahayaks*), and district planners with an ultra-accessible, high-contrast agro-meteorological dashboard. It transforms complex two-stage machine learning downscaling predictions and live atmospheric forecasts into actionable farming decisions.

### Core Implemented Capabilities:
1. **Statewide 3,339 Gram Panchayat Autocomplete & District Selection:** Real-time debounced search across all 22 rural districts of West Bengal, querying `/v1/statewide/panchayats` to instantly locate and inspect any Gram Panchayat with verified Local Government Directory (LGD) codes and centroid GPS coordinates. Preset dropdown support provides quick navigation for the core surveyed pilot panchayats.
2. **Live Dynamic Weather Telemetry:** Real-time status indicator evaluating `data.is_live_dynamic` from `/v1/forecast`, displaying dynamic Open-Meteo ECMWF/GFS meteorological ingestion downscaled by the TerraMind Hurdle model with 15-minute TTL caching and graceful offline fallback.
3. **Interactive Spatial Map:** React-Leaflet spatial comparison canvas visualizing microclimate variations, block centres, and Gram Panchayat centroids with animated pan-and-focus selection.
4. **Agronomic Advisory Intelligence:** Rules-driven advisories evaluated against crop type (Paddy, Vegetables) with priority classification (*High Attention* vs *Normal*).
5. **Future Multichannel Integration (Roadmap):** Voice audio playback (TTS) and instant WhatsApp bulletin dissemination scheduled for Phase 4 deployment.

---

## 2. Directory Structure & Key Files

```text
frontend/
├── index.html                      # HTML entry point and viewport configuration
├── package.json                    # Dependencies: React 19.2, React-Leaflet 5, Leaflet 1.9, Vite 8
├── vite.config.js                  # Vite 8 bundler configuration with React plugin
├── vercel.json                     # Vercel SPA client-side rewrite rules
├── eslint.config.js                # ESLint 10 flat configuration
├── .env                            # API base URL configuration (VITE_API_BASE_URL)
├── public/
│   ├── favicon.svg                 # TerraMind browser favicon
│   └── icons.svg                   # Vector icon definitions
├── src/
│   ├── main.jsx                    # React root entry point (StrictMode mount)
│   ├── App.jsx                     # Core application component (State, Search, TTS, Cards, Telemetry)
│   ├── App.css                     # High-contrast mobile-first stylesheet (WCAG sunlight readable)
│   ├── ComparisonMap.jsx           # Interactive React-Leaflet spatial comparison map
│   ├── index.css                   # Global base resets and typography
│   └── assets/                     # Static graphics (hero.png, react.svg, vite.svg)
└── README.md                       # Workspace technical documentation
```

*Note: Component modularization into `src/components/` (`ForecastCard.jsx`, `StatewideSearch.jsx`, etc.) and `src/services/` (`api.js`) is tracked as a technical debt backlog item to decouple `App.jsx`.*

---

## 3. Local Development & Deployment

### Prerequisites
- Node.js >= 18.0.0 (Node 20+ recommended)
- npm >= 9.0.0

### Setup & Run Commands

```bash
# 1. Navigate to frontend workspace
cd frontend

# 2. Install dependencies
npm install

# 3. Start local development server (http://localhost:5173)
npm run dev

# 4. Build for production (outputs to frontend/dist)
npm run build

# 5. Preview production build locally
npm run preview

# 6. Run ESLint code checks
npm run lint
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
| `/v1/forecast` | `GET` | `panchayat_id`, `days=5`, `lang=en`, `crop`, `live` | Retrieves 5-day downscaled rainfall (P10/P50/P90), temperatures, advisories, and live dynamic weather telemetry (`is_live_dynamic`). |
| `/v1/statewide/panchayats` | `GET` | `search`, `limit=6` | Real-time debounced autocomplete search across all 3,339 Gram Panchayats in West Bengal. |
| `/v1/statewide/districts` | `GET` | — | *(Planned)* Filter Panchayats by district hierarchy across all 22 rural districts. |
| `/v1/statewide/stats` | `GET` | — | *(Planned)* Header telemetry counter (3,339 Panchayats, 22 Districts). |

---

## 5. UI Workflows

1. **Statewide Search & Selection:**
   - Farmer or official types a Gram Panchayat name (e.g., "Banchukamari", "Falakata") into the search bar.
   - Matching Panchayats appear in the dropdown with Block and District context.
   - Selecting a GP loads its 5-day AI forecast and displays an LGD coordinate badge (`📍 {panchayat_name} | Block: {block} • District: {district} • LGD: {code} ({lat}°N, {lon}°E)`).
   - Core surveyed pilot panchayats can also be selected directly via the quick-select dropdown.
2. **Live Dynamic Weather Badge:**
   - Visual telemetry displays `"LIVE DYNAMIC WEATHER"` with `"AI Downscaled (Open-Meteo ECMWF/GFS)"` when real-time feeds are active, or `"V2 MODEL ACTIVE"` / `"V2 FALLBACK ACTIVE"` during offline or degraded conditions.
3. **Interactive Comparison Map:**
   - Visualizes localized microclimates and downscaled variances across Gram Panchayats.
4. **Future Delivery (Roadmap):**
   - Spoken audio advisory streaming and WhatsApp community sharing buttons will be connected in Phase 4.
