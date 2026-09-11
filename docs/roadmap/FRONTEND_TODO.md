# TerraMind Frontend Roadmap & Task Tracking

> **Owner:** Member 1 — Frontend Engineer  
> **Framework:** React 19 (`^19.2.8`) + Vite 8 (`^8.2.2`)  
> **Deployment:** Vercel Production [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)  
> **Language:** Strictly English (Zero Bengali text, clean international presentation)  
> **Default Panchayat:** Amdanga (`WB_107778`, North 24 Parganas)  
> **Last Synchronized:** 2026-09-10 (Post Modular Rebuild & Quantile Uncertainty Integration)

---

## 1. Milestone Tracking

### ✅ Completed Milestones
- [x] **Component Modularization Refactoring:**
  - Decomposed monolithic `App.jsx` into clean, single-responsibility components:
    - `src/services/api.js` (centralized API fetch client with error handling)
    - `src/components/SearchBar.jsx` (debounced 3,339 GP search + 22-district filter)
    - `src/components/CurrentWeatherHero.jsx` (hero weather card, crop selector, live/offline toggle)
    - `src/components/QuantileForecastList.jsx` (5-day cards with P10/P50/P90 uncertainty bars)
    - `src/components/AgronomicAlerts.jsx` (prioritized agricultural advisory cards)
    - `src/components/SystemStatsFooter.jsx` (2.44M rows, 3,339 GPs telemetry banner)
    - `src/utils/formatters.js` (date formatting and operational action chip heuristics)
  - Result: `npm run lint` passes with 0 errors, 0 warnings. Production build executes in <250ms.
- [x] **Full Quantile Uncertainty Visualization (P10 / P50 / P90):**
  - Rendered horizontal confidence interval bars displaying minimum dry bound (P10), expected median (P50), and worst-case runoff risk (P90).
- [x] **Operational Agronomic Action Chips:**
  - Direct actionable decision pills on each daily forecast card:
    - 🚫 **Do Not Spray:** *High risk of pesticide wash-off*
    - ✅ **Fertilizer Safe:** *Light rain aids nitrogen absorption*
    - 🌧️ **Check Drainage:** *Keep field drainage channels clear*
    - 🌾 **Protect Harvest:** *Cover reaped paddy to avoid spoilage*
    - ☀️ **Heat Stress Alert:** *Schedule irrigation early morning*
    - ⚠️ **Blast Risk:** *Favorable fungal humidity conditions*
- [x] **Live Dynamic Weather Toggle Switch:**
  - Integrated toggle switch between live dynamic Open-Meteo (ECMWF/GFS) Hurdle downscaling and offline Parquet baseline.
- [x] **Statewide 3,339 Gram Panchayat Autocomplete & District Filter:**
  - Real-time debounced search calling `GET /v1/statewide/panchayats` + `GET /v1/statewide/districts`.
  - Active breadcrumb card displaying LGD code, elevation (m), and soil texture.
- [x] **Statewide Data Lake Telemetry Banner:**
  - Ingests `GET /v1/statewide/stats` to verify 2.44M records and QA status.
- [x] **Language Normalization:**
  - 100% pure English text across the entire frontend (0 non-ASCII / Bengali characters).
- [x] **Google-Style 24-Hour Hourly Weather & Spray Window Slider (`HourlyWeatherSlider.jsx`):**
  - **24-Hour Horizontal Time Slider:** Scrollable carousel with daylight/night markers, condition icons, and current hour indicator.
  - **Dynamic Multi-Day Date Synchronization:** Synchronized with the 5-day forecast horizon (Today, Tomorrow, Day +2, Day +3, Day +4).
  - **Day-Selector Navigation Bar:** Interactive day pill buttons in the card header providing instant switching across all 5 days.
  - **3 Interactive Metric Tabs:**
    - **Temperature Tab:** Elevation-adjusted hourly curve (-6.5°C / 1,000m lapse rate).
    - **Precipitation Tab:** Hourly rain probability bars and accumulation in millimeters.
    - **Wind & Spray Safety Tab:** Hourly wind speed with color-coded safety badges (`Optimal`, `Caution`, `Rain Risk`, `Wind Drift`).
  - **Operational Spray Window Banner:** Auto-synthesizes contiguous daytime spraying window and dynamic farm work advice for the active date.
  - **Dual Live/Offline Guarantee:** Connects to live ECMWF/GFS stream in Live mode, and automatically synthesizes a physical solar diurnal curve in Offline mode with an inline quick-toggle button.
- [x] **Browser Geolocation & LocalStorage Preference Memory:**
  - **1-Click GPS Auto-Detect Button:** Interactive "📍 Use My Location" in the search row queries device GPS coordinates.
  - **Vectorized Haversine Resolution:** Calls `GET /v1/statewide/nearest` to locate the closest Gram Panchayat in <15ms across all 3,339 GPs.
  - **Session Memory (`localStorage`):** Remembers the user's selected Gram Panchayat (`terramind_panchayat_id`, `terramind_panchayat_meta`) and active crop (`terramind_crop`) across browser restarts and page refreshes.
  - **GPS Distance Tag:** Renders exact distance from user coordinates (e.g. `GPS Distance: 14.6 km away`) directly in the active Gram Panchayat card.
- [x] **Self-Contained Vector SVG Icons (`WeatherIcon.jsx`):**
  - Pure inline vector SVGs eliminating external Google CDN dependencies, broken images, and text wrapping glitches.
- [x] **Clean 3-Element Search Bar (`SearchBar.jsx`):**
  - Restored streamlined layout: District filter dropdown, debounced Gram Panchayat search with reliable click selection, and GPS auto-detect button.

---

## 2. Active Priorities

*(All high-priority core presentation features are implemented and verified. Platform is in polish and review stage.)*

---

## 3. Items On Hold (Backlog)

### ✅ Dynamic Statewide Spatial Leaflet Comparison Map
- **Status:** **COMPLETED**
- Dynamic Leaflet GIS comparison map fully integrated into `frontend/src/App.jsx`.
- Dynamically queries and renders all sibling Gram Panchayats in the active block via statewide registry.
- Side-by-side coarse regional forecast vs. localized downscaled Panchayat predictions.
- Full date-horizon synchronization, smooth animated map transitions (`map.flyTo`), and "Inspect This Panchayat" quick-selection popups.

### On Hold: Offline Mode & PWA
- **Status:** **ON HOLD**  
- System is operating in 100% online dynamic mode. PWA caching and service workers will be scheduled in a subsequent phase.

### On Hold: Multichannel Voice (TTS) & WhatsApp Dissemination
- **Status:** **ON HOLD (Phase 4)**  
- Audio voice streaming and WhatsApp community sharing buttons are staged for post-hackathon pilot expansion.
