# TerraMind — Feature Roadmap & Updates Needed

> **Target:** Smart India Hackathon (SIH) prototype evolution to full-scale rural deployment.  
> **Status Document:** Living document for future features, ML upgrades, and architectural enhancements.

---

## 🚀 Priority 1: Immediate Hackathon Wins (High Demo Value)

These features require low effort but have a massive visual and practical impact during presentations and jury evaluations.

- [ ] **Voice / Text-to-Speech in Bengali ("অডিও শুনুন"):**
  - Add an audio playback button on the frontend cards using the browser's native Web Speech API (`SpeechSynthesis`) or an Indian language TTS model (e.g., AI4Bharat / Bhashini API).
  - Enables illiterate and elderly farmers to listen to advisories in spoken colloquial Bengali.
- [ ] **One-Click WhatsApp Share Button:**
  - Add a button: *"হোয়াটসঅ্যাপে শেয়ার করুন"* (Share on WhatsApp).
  - Pre-formats today's panchayat forecast and Bengali advisory into a clean WhatsApp message for easy forwarding to local Krishi (farmer) WhatsApp groups.
- [ ] **Offline-First PWA (Progressive Web App):**
  - Add a Web App Manifest and Service Worker in the Vite frontend.
  - Allows farmers to install TerraMind directly to their Android home screen and view cached advisories even when rural mobile data is patchy.

---

## 🌱 Priority 2: Agricultural Intelligence & Crop Health

Move beyond raw weather figures into proactive agronomic protection.

- [ ] **Pest & Disease Prediction Models:**
  - Build rule-based triggers and ML classifiers for local diseases (e.g., **Paddy Blast**, **Sheath Blight**, and potato late blight).
  - Trigger conditions: High-humidity streaks (>85% for ≥3 consecutive days) combined with temperatures between 24°C–30°C.
- [ ] **Actionable Fertilizer & Chemical Spray Windows:**
  - Instead of general weather warnings, calculate clear operational windows:
    - *"Urea Application: ❌ Avoid for 48 hours (rain runoff risk)."*
    - *"Pesticide Spray: ✅ Safe between 8:00 AM – 11:00 AM tomorrow."*
- [ ] **Satellite Crop Health (Sentinel-2 NDVI & Soil Moisture):**
  - Integrate free Copernicus Sentinel-2 multispectral imagery.
  - Display NDVI (Normalized Difference Vegetation Index) maps to identify crop stress or dry patches inside individual panchayat borders.

---

## ⛈️ Priority 3: Machine Learning & Meteorological Refinements

### 🔍 Current Model Diagnostic (from `v1_3_metadata.pkl`)
* **Event Detection is Solid (POD = 0.91):** Detects rain events accurately (91% detection).
* **Extreme Rain Underestimation (Heavy-rain RMSE ≈ 28.05 mm, MAE ≈ 26.26 mm):** Standard MSE loss pulls heavy monsoon downpours toward the mean.
* **Terrain is Nearly Irrelevant (<1% feature importance):** Gangetic plains elevation varies by only 5–15 m (no orographic lift to trigger localized rain).
* **Training Dataset Too Brief (Jan 2024 – Aug 2024):** Only ~8 months of data, containing fewer than 30 heavy rain events.

---

### 🛠️ Concrete Technical Improvement Plan

- [ ] **1. Log-Transform & Tweedie Loss Function (Fixes Underestimation):**
  - **Issue:** MSE / L2 loss penalizes large deviations symmetrically, forcing the model to predict safe median values.
  - **Action:**
    - Train the residual model on $\log(1 + \text{rain})$ to preserve high-magnitude spikes without distortion.
    - Switch XGBoost objective to Tweedie regression (`objective="reg:tweedie"`, `tweedie_variance_power=1.5`), which naturally models zero-inflated, right-skewed compound Poisson-Gamma distributions like daily rainfall.

- [ ] **2. Ingest Dynamic Atmospheric Physics (Replace Flat Terrain):**
  - **Issue:** Static terrain features (`elevation`, `slope_deg`, `distance_to_river_m`) contribute <1% feature importance.
  - **Action:** Ingest convective atmospheric variables from Open-Meteo / ERA5:
    - **CAPE (Convective Available Potential Energy):** Predicts sudden convective thunderstorm / Nor'wester (Kalbaishakhi) onset.
    - **Total Column Precipitable Water:** Total moisture content in the vertical atmosphere.
    - **850 hPa Wind Vectors ($U$ and $V$ components):** Direction and speed of monsoon cloud drift.

- [ ] **3. Expand Training Historical Horizon to 5–10 Years (2015–2024):**
  - **Issue:** 8 months of data lacks enough cyclone, depression, and severe monsoon patterns.
  - **Action:** Pull 10 full years of CHIRPS (0.05°) and ERA5 reanalysis to give the model hundreds of extreme weather events across seasons.

- [ ] **4. 3-Stage "Hurdle" Architecture with Quantile Uncertainty:**
  - **Architecture Flow:**
    ```text
    Input Features
          │
          ├─► Stage 1: Rain Occurrence Classifier (Binary: Rain / Dry)
          │
          ├─► Stage 2: Heavy Rain Trigger Classifier (Is Rain > 25 mm?)
          │
          └─► Stage 3: Multi-Quantile Regressor
                ├── Lower Bound (P10)
                ├── Median Expected (P50)
                └── Upper Extreme Bound (P90)
    ```
  - If Stage 2 flags an extreme event, the system automatically surfaces the **P90** value rather than an averaged estimate.

- [ ] **5. Upwind Spatial Neighbor Lags:**
  - Calculate directional spatial neighbor lags:
    $$\text{neighbor\_rain\_lag1} = \text{mean}(\text{rain in upwind neighboring panchayats yesterday})$$
  - Matches the physical movement of monsoon clouds travelling southwest to northeast across the block.

- [ ] **6. Ground-Truth Calibration (Local AWS / Rain Gauges):**
  - Ingest ground-truth station observations from local Automatic Weather Stations (AWS) or Gram Panchayat rain gauges to calibrate satellite products (CHIRPS/IMERG).

- [ ] **7. Transition from "Degraded" Fallback to True Downscaling:**
  - Validate multi-day downscaling accuracy across spatial points to safely remove the `degraded: true` operational flag.

---

## 🏛️ Priority 4: Panchayat Administration & Disaster Management

Features designed for Gram Panchayat Pradhans, BDOs, and Agricultural Extension Officers.

- [ ] **Waterlogging & Flood Accumulation Heatmap:**
  - Leverage `elevation_dem_m` and `distance_to_river_m` to simulate surface water pooling and drainage bottlenecks following heavy rains (>30 mm).
- [ ] **Panchayat Broadcast & Emergency Alert System:**
  - Enable authenticated Panchayat officials to post hyper-local bulletins (e.g., *"Canal sluice gates opening at 10 AM"*, *"Subsidized seed distribution on Thursday"*).
- [ ] **Crop Damage Assessment Reports:**
  - Automatically export PDF incident summaries after hailstorms or flash floods for insurance claims under Pradhan Mantri Fasal Bima Yojana (PMFBY).

---

## 🗺️ Priority 5: Nationwide Scalability & Architecture

Take TerraMind from Amdanga block to all of India.

- [ ] **Automated Panchayat Onboarding Engine:**
  - Dynamic boundary retrieval: Select State ➔ District ➔ Block to auto-import administrative boundaries from Survey of India / OpenStreetMap GeoJSONs.
  - Automatically fetch regional SoilGrids data and terrain DEMs for newly registered panchayats.
- [ ] **Automated Ingestion Pipeline (Cron / Scheduler):**
  - Set up automated daily cron jobs to fetch fresh Open-Meteo forecasts at 06:00 IST every morning and regenerate advisory contexts.
- [ ] **Dockerization & Production Deployment:**
  - Create `Dockerfile` and `docker-compose.yml` defining the FastAPI backend and Nginx-served Vite frontend for 1-click cloud deployment.
