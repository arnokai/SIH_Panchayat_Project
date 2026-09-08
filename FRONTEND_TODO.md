# TerraMind Frontend Roadmap & Task Tracking

> **Owner:** Member 1 — Frontend Engineer  
> **Framework:** React 19 (`^19.2.8`) + Vite 8 (`^8.2.2`) + React-Leaflet 5 (`^5.0.0`)  
> **Deployment:** Vercel Production [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)  
> **Last Synchronized:** 2026-09-08 (Post Statewide Parquet & Live Open-Meteo Integration)

---

## 1. Milestone Tracking

### Completed Milestones
- [x] **Statewide 3,339 Gram Panchayat Autocomplete:**
  - Real-time debounced search calling `GET /v1/statewide/panchayats?search=...&limit=6`.
  - Dropdown rendering GP name, Block name, and District name.
  - Selected statewide GP badge displaying LGD code and verified centroid latitude/longitude.
  - Automatic fallback mapping to surveyed pilot coordinates for Amdanga Panchayats.
- [x] **Live Dynamic Weather Status Badge:**
  - Integrated status indicator reflecting real-time Open-Meteo ECMWF/GFS meteorological ingestion downscaled by the Hurdle model (`data.is_live_dynamic`).
  - Graceful fallback messaging for V2 static model and degraded mode.
- [x] **Bengali Voice / Text-to-Speech ("অডিও শুনুন"):**
  - Native browser Web Speech API implementation targeting Bengali (`bn-IN`).
  - Intelligent voice discovery filtering for Bengali speech synthesizers.
  - Per-card play/stop controls, per-advisory buttons, and full sequential audio player ("সব পরামর্শ শুনুন").
- [x] **One-Click WhatsApp Community Dissemination:**
  - WhatsApp Markdown bulletin generator with crop advisories, rainfall, temperatures, and portal links.
  - Dedicated share buttons on daily forecast cards and action advisories.
- [x] **Interactive Comparison Map (Pilot Baseline):**
  - React-Leaflet spatial map plotting Amdanga Block centre and 8 Panchayat centroids.
  - Day selector synchronized with 5-day forecast cards.
- [x] **Core Stack Modernization:**
  - Migrated to React 19.2 and Vite 8 with zero compilation or lint errors.

---

## 2. Active Priorities & Backlog

### Priority 1: High-Impact Jury & Operational Features
- [ ] **Live Dynamic Weather Toggle Switch:**
  - Add an intuitive UI toggle in the selector card to allow switching between `live=true` (Live Open-Meteo 5-day ECMWF/GFS forecast) and `live=false` (Offline V2 Hurdle model).
- [ ] **Offline-First Progressive Web App (PWA):**
  - Install and configure `vite-plugin-pwa`.
  - Add Web App Manifest (`manifest.json`) with agriculture icons, green theme (`#06372b`), and standalone display mode.
  - Implement ServiceWorker cache strategy (`StaleWhileRevalidate`) for `/v1/forecast` and `/v1/statewide/panchayats`.
  - Display offline banner when `navigator.onLine === false`.
- [ ] **Full Quantile Uncertainty Visualization (P10 / P50 / P90):**
  - Render an intuitive confidence range bar on each daily card displaying:
    - Minimum likely rain (P10)
    - Median expected rain (P50)
    - Worst-case downpour (P90)

### Priority 2: Statewide Exploration & Spatial Depth
- [ ] **Cascading Statewide District & Block Selector:**
  - Consume `GET /v1/statewide/districts` to provide hierarchical district-first browsing (22 Districts -> 342 Blocks -> 3,339 GPs) alongside the search bar.
- [ ] **Statewide Spatial Map View:**
  - Expand `ComparisonMap.jsx` beyond Amdanga to render district boundary overlays and dynamically center on any selected statewide Gram Panchayat.
- [ ] **Operational Agronomic Action Pills:**
  - Render dedicated high-contrast visual chips for key field operations:
    - 🚫 **Urea Application:** *Avoid for 48 hrs (Runoff risk)*
    - 🚜 **Field Spraying:** *Safe tomorrow 8:00 AM – 11:00 AM*
    - 💧 **Irrigation:** *Not needed (Rain expected)*

### Priority 3: Architecture & Polish
- [ ] **Component Modularization Refactoring:**
  - Decompose monolithic `App.jsx` (1,193 lines) into modular components:
    - `src/components/StatewideSearch.jsx`
    - `src/components/ForecastCard.jsx`
    - `src/components/AdvisorySection.jsx`
    - `src/components/SystemTelemetry.jsx`
    - `src/services/api.js`
- [ ] **Language Toggle & Persistence:**
  - Add Bengali (`বাংলা`) / English (`English`) toggle switch with `localStorage` persistence.
- [ ] **Printable Notice Board Bulletin:**
  - Print-optimized CSS stylesheet for Gram Panchayat notice boards and Common Service Centres (CSCs).

---

## 3. Bug Fixes & Technical Debt

- [x] Fixed ESLint configuration for React 19 flat config in `eslint.config.js`.
- [ ] Fix execution bit permissions on `frontend/node_modules/.bin/eslint` for seamless CI/CD `npm run lint` execution.
- [ ] Standardize API error handling with retry toast alerts when backend is warming up on Render cold start.
