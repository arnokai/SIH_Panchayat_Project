# TerraMind — Feature Roadmap & 4-Member Action Plan

> **Target:** Smart India Hackathon (SIH 2026 — Problem Statement SIH26074)  
> **Status:** Active development with cloud-deployed prototype (Vercel + Render).

---

## ✅ Completed Milestones

- [x] **4-Member Modular Codebase Reorganization:**
  - Separated project into dedicated, conflict-free workspaces: `frontend/`, `backend/`, `rules/`, `ml/`, `data_pipeline/`, `docs/`, and `tests/`.
  - Added root `api.py` backward-compatibility shim guaranteeing uninterrupted Render cloud deployments.
  - Resolved all relative and project-root path imports with fallback support.
  - Verified all integration tests (`test_advisory_context.py`, `test_advisory_rules.py`, `test_forecast_advisories.py`) pass 100% cleanly.
- [x] **Live Cloud Deployments:**
  - Frontend live on Vercel: [sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)
  - Backend live on Render: [sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)
  - Interactive API docs: [sih-panchayat-project.onrender.com/docs](https://sih-panchayat-project.onrender.com/docs)
- [x] **Bilingual Advisory Engine (`rules/rules.yaml`):**
  - Integrated 5 core SIH handbook rules (`no_spray_rain`, `heat_stress`, `blast_disease_risk`, `sandy_soil_dry_spell`, `harvest_rain`) + 3 extensions (`moderate_rain`, `light_rain`, `dry_day`).
  - Tested across 5,848 historical weather rows.

---

## 🚀 Priority 1: High-Impact Demo Additions — [Member 1: Frontend]

> 📖 **Full Workspace Guide & Technical Tasks:** See [frontend/README.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/frontend/README.md) or [FRONTEND_TODO.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/FRONTEND_TODO.md).

These features require low effort but have a massive visual and practical impact during jury evaluation.

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

## 🌱 Priority 2: Agricultural Intelligence — [Member 2: Backend & Rules]

> 📖 **Full Workspace Guide & Technical Tasks:** See [backend/README.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/backend/README.md) or [BACKEND_TODO.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/BACKEND_TODO.md).

Move beyond raw weather figures into proactive agronomic protection.

- [ ] **Pest & Disease Prediction Models:**
  - Build rule-based triggers and ML classifiers for local diseases (e.g., **Paddy Blast**, **Sheath Blight**, and potato late blight).
  - Trigger conditions: High-humidity streaks (>85% for ≥3 consecutive days) combined with temperatures between 24°C–30°C.
- [ ] **Actionable Fertilizer & Chemical Spray Windows:**
  - Instead of general weather warnings, calculate clear operational windows:
    - *"Urea Application: ❌ Avoid for 48 hours (rain runoff risk)."*
    - *"Pesticide Spray: ✅ Safe between 8:00 AM – 11:00 AM tomorrow."*
- [ ] **KVK Scientist Rule Verification Interface:**
  - Dedicated lightweight dashboard endpoint for local KVK scientists to review and sign off on threshold values in `rules/rules.yaml`.

---

## ⛈️ Priority 3: Machine Learning & Downscaling Refinements — [Member 3: AI / ML & Data]

> 📖 **Full Workspace Guide & Technical Tasks:** See [ml/README.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/ml/README.md) or [ML_TODO.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/ML_TODO.md).

### 🔍 Current Model Diagnostic (from `ml/models/v1_3_metadata.pkl`)
* **Event Detection is Solid (POD = 0.91):** Detects rain events accurately (91% detection).
* **Extreme Rain Underestimation (Heavy-rain RMSE ≈ 28.05 mm, MAE ≈ 26.26 mm):** Standard MSE loss pulls heavy monsoon downpours toward the mean.
* **Terrain is Nearly Irrelevant in Flat Delta (<1% feature importance):** Gangetic plains elevation varies by only 5–15 m (no orographic lift).
* **Training Dataset Too Brief (Jan 2024 – Aug 2024):** Only ~8 months of data, containing fewer than 30 heavy rain events.

### 🛠️ Concrete Technical Improvement Plan
- [ ] **1. Log-Transform & Tweedie Loss Function (Fixes Underestimation):**
  - Train the residual model on $\log(1 + \text{rain})$ to preserve high-magnitude spikes without distortion.
  - Switch XGBoost objective to Tweedie regression (`objective="reg:tweedie"`, `tweedie_variance_power=1.5`), naturally modeling zero-inflated, right-skewed compound Poisson-Gamma distributions.
- [ ] **2. Ingest Dynamic Atmospheric Physics (Replace Flat Terrain):**
  - Ingest convective atmospheric variables from Open-Meteo / ERA5:
    - **CAPE (Convective Available Potential Energy):** Sudden convective thunderstorm / Kalbaishakhi onset.
    - **Total Column Precipitable Water:** Total moisture content in vertical atmosphere.
    - **850 hPa Wind Vectors ($U$ and $V$ components):** Direction and speed of monsoon cloud drift.
- [ ] **3. Expand Training Historical Horizon to 5–10 Years (2015–2024):**
  - Ingest 10 full years of CHIRPS (0.05°) and ERA5 reanalysis to capture hundreds of extreme monsoon and cyclone events.
- [ ] **4. 3-Stage "Hurdle" Architecture with Quantile Uncertainty (P10 / P50 / P90):**
  - Stage 1: Rain Occurrence (Binary)
  - Stage 2: Heavy Rain Trigger (>25 mm)
  - Stage 3: Multi-Quantile Regressor (P10, P50, P90 confidence bounds).
- [ ] **5. Transition from "Degraded" Fallback to Validated Downscaling:**
  - Safely transition `degraded: false` once multi-day spatial downscaling outperforms coarse baselines.

---

## 🏛️ Priority 4: Panchayat Administration & Disaster Management — [Member 4: Manager & DevOps]

> 📖 **Full Workspace Guide & Technical Tasks:** See [docs/DEVOPS_README.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/docs/DEVOPS_README.md) or [DEVOPS_TODO.md](file:///home/arnokai/Projects/SIH_Panchayat_Project/DEVOPS_TODO.md).

- [ ] **Waterlogging & Flood Accumulation Heatmap:**
  - Leverage `elevation_dem_m` and `distance_to_river_m` to simulate surface water pooling following heavy rains (>30 mm).
- [ ] **Automated Daily Ingestion Scheduler (GitHub Actions / Cron):**
  - Set up automated daily cron jobs at 05:30 IST to fetch fresh Open-Meteo forecasts and pre-generate panchayat advisories.
- [ ] **Crop Damage Assessment Reports (PMFBY Insurance Export):**
  - PDF export of incident summaries following extreme rain or heatwaves for insurance loss verification.
- [ ] **Presentation Preparation & Final Rehearsals:**
  - Align the mandated 6-slide SIH presentation deck according to the handbook guidelines.
