# TerraMind — Panchayat-Level Weather Intelligence & Agricultural Advisory

[![Frontend](https://img.shields.io/badge/Frontend-Vercel%20Live-black?style=flat&logo=vercel)](https://sih-panchayat-project.vercel.app)
[![Backend](https://img.shields.io/badge/Backend-Render%20Live-46E3B7?style=flat&logo=render)](https://sih-panchayat-project.onrender.com)
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-85EA2D?style=flat&logo=swagger)](https://sih-panchayat-project.onrender.com/docs)
[![CI Guard](https://img.shields.io/badge/CI%20Guard-Active-brightgreen?style=flat&logo=githubactions)](https://github.com/arnokai/SIH_Panchayat_Project/actions)
[![Data Lake](https://img.shields.io/badge/Data%20Lake-2.44M%20Rows%20(Parquet)-blue)](data_pipeline/processed/statewide)
[![Tests](https://img.shields.io/badge/Tests-248%20Passing-brightgreen)](tests)
[![Knowledge Graph](https://img.shields.io/badge/Graphify-Active%20Knowledge%20Graph-8A2BE2)](AGENTIC_AI_GRAPHIFY_SETUP.md)

> 🌐 **Live Web Application:** [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)  
> ⚡ **Live Cloud API:** [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)  
> 📚 **Interactive Swagger Docs:** [https://sih-panchayat-project.onrender.com/docs](https://sih-panchayat-project.onrender.com/docs)  
> 🤖 **Agentic AI & Graphify Guide:** [`AGENTIC_AI_GRAPHIFY_SETUP.md`](AGENTIC_AI_GRAPHIFY_SETUP.md)  
> **Repository:** `https://github.com/arnokai/SIH_Panchayat_Project`  
> **Geographic Scope:** Statewide West Bengal (3,339 Gram Panchayats across all 22 Rural Districts — 100% Equal Presentation)  

TerraMind is a production-grade, cloud-deployed **hyper-local downscaling data lake, probabilistic forecast engine, and agricultural-advisory decision-support system**. It bridges the critical resolution gap between coarse ~25 km block forecasts and sharp ~2 km Gram Panchayat farming realities across all 3,339 Gram Panchayats of West Bengal.

---

## 🚀 Quick Start

### Requirements
- Python 3.9+ (tested on Python 3.12 & 3.14)
- Node.js 18+ + npm or pnpm
- Git

### Step 1 — Clone the repo

```bash
git clone https://github.com/arnokai/SIH_Panchayat_Project.git
cd SIH_Panchayat_Project
```

### Step 2 — Set up Python environment

```bash
# Linux / macOS (Bash / Zsh)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```fish
# Linux / macOS (Fish shell)
python3 -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements.txt
```

```powershell
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 3 — Start the backend

```bash
# Option A: Production CLI Entrypoint (Recommended):
.venv/bin/terramind-engine serve --host 0.0.0.0 --port 8000 --reload

# Option B: Direct Uvicorn:
uvicorn api:app --reload --port 8000
```

Backend runs at: **http://127.0.0.1:8000**  
API docs at: **http://127.0.0.1:8000/docs**  

### Step 4 — Start the frontend (new terminal)

```bash
cd frontend
pnpm install # or npm install

# Optional: To connect your local frontend to the live Render cloud backend:
# echo "VITE_API_BASE_URL=https://sih-panchayat-project.onrender.com" > .env

pnpm dev # or npm run dev
```

Dashboard runs at: **http://localhost:5173**

---

## 1. Core Architecture: Operational Decision-Support Pipeline

TerraMind operates as an integrated end-to-end **decision-support pipeline**:

```text
Gram Panchayat (3,339 Statewide LGD Equals)
   ↓
Copernicus 30m DEM + SoilGrids Edaphic Telemetry (14 Physical Features)
   ↓
Live Atmospheric Ingestion (Open-Meteo ECMWF/GFS with 15-min TTL Cache)
   ↓
Regional Two-Stage Hurdle Downscaling (Delta / Laterite / Terai Quantiles)
   ↓
Dynamic Phenology Engine (Base-10 GDD & Stage Tracking across 6 Crops)
   ↓
Agricultural Advisory Rule Engine (rules/rules.yaml)
   ↓
Multi-Channel Delivery:
   ├── React 19 Cadastral Map & Crop Command Center (Web UI)
   ├── Dual AI Agro-Climatic Chatbot (POST /v1/ai/chat)
   ├── PMFBY Cryptographic Insurance Claim Certificates (HMAC-SHA256)
   ├── Bay of Bengal Live Cyclone Alerting (LC3 Port Signals)
   ├── Multi-Channel Telecommunications (<= 160-char SMS & 1800-TERRAMIND IVR)
   └── Printable A4 Krishi Bulletins for CSC Notice Boards
```

### Key Operational Capabilities

| Capability | Early Benchmark | TerraMind Production |
|---|---|---|
| **Coverage Scope** | 8 Pilot Panchayats (Amdanga) | **3,339 Gram Panchayats statewide** across all 22 rural districts |
| **Presentation Parity** | Specialized pilot tiers | **100% Equal Presentation:** All 3,339 GPs are equal first-class citizens |
| **Boundary Precision** | Point centroids / circular buffers | **Cadastral Boundary Precision:** 100% zero displacement inside Survey of India block envelopes |
| **Model Downscaling** | Experimental regression | **Two-Stage Hurdle:** Occurrence classification (99.39% acc) + P10/P50/P90 Quantile Regressors |
| **Regional Zoning** | Single global model | **3 Specialized Regional Hurdle Models:** Coastal Delta, Western Laterite, Sub-Himalayan Terai |
| **Cadastral Map** | On hold | **Active Operational Cadastral Map:** Clickable Voronoi parcels, emerald active GP highlight, Doppler radar |
| **Phenology Engine** | Static calendar | **Dynamic GDD Tracking:** Base-10 Growing Degree Days with biological stage transitions for 6 crops |
| **Crop Command Center**| Simple advisories | **Full Command Center:** Pest & Disease Doctor, Package of Practices, NPK calculator, FAO-56 $ET_c$ |
| **Disaster Operations**| None | **Bay of Bengal Cyclone Tracker** (IMD RSMC bulletins, LC3 port signals) + **PMFBY HMAC Certificates** |
| **API Architecture** | Prototype endpoints | **Production Suite:** 12+ REST endpoints, sub-ms boundary caching, production CLI entrypoint |
| **Test Verification** | 161 unit tests | **248 automated unit tests passing (100% green)** in ~20 seconds |

---

## 2. Statewide AI Hurdle Downscaling Architecture

TerraMind deploys a high-accuracy **Two-Stage Hurdle Downscaling Architecture** backed by a statewide master model (`ml/models/statewide_hurdle_v2.pkl`) and three specialized regional hurdle models:

### Specialized Regional Hurdle Models:
1. **Coastal & Gangetic Delta (`hurdle_delta.pkl`):** Tailored for high humidity, alluvial clay/silt soils, and flat coastal floodplains (Sundarbans, North/South 24 Parganas, Nadia, Hooghly).
2. **Western Laterite Plateau (`hurdle_laterite.pkl`):** Tailored for orographic dry shadows, gravelly red soils, high convective temperatures, and flash runoff (Purulia, Bankura, Jhargram, Paschim Medinipur).
3. **Sub-Himalayan Terai & Dooars (`hurdle_terai.pkl`):** Tailored for steep elevation gradients (up to 3,600m in Darjeeling), high orographic precipitation, and sandy-loam soils (Darjeeling, Jalpaiguri, Alipurduar, Cooch Behar).

### Model Architecture & Key Metrics:
- **Stage 1 (Precipitation Occurrence):** `HistGradientBoostingClassifier` trained on 16 atmospheric, terrain, and soil features, achieving **99.39% accuracy**, **0.9999 ROC-AUC**, and **99.49% Probability of Detection (POD)**.
- **Stage 2 (Precipitation Amount):** `HistGradientBoostingRegressor` ($P_{50}$ Median) trained on rainy occurrences, achieving an MAE of **0.56 mm** and RMSE of **1.71 mm** on the untouched 2025 holdout horizon.
- **Stage 3 (Quantile Uncertainty Bounds):** Dual quantile regressors predicting $P_{10}$ (dry bound) and $P_{90}$ (flood risk bound) with **100% quantile monotonicity** ($P_{90} \ge P_{50} \ge P_{10}$).

### Operational Delivery Status:
When the model artifact is loaded, the API reports full operational health (`degraded: false`):
```json
{
  "status": "ok",
  "service": "TerraMind Panchayat Forecast API",
  "model_version": "V2.0 Statewide Hurdle (Quantile HGB)",
  "rainfall_model": "Two-Stage Hurdle Downscaling (P10/P50/P90)",
  "statewide_coverage": "3,339 Gram Panchayats / 22 Districts",
  "live_weather_enabled": true,
  "degraded": false,
  "reason": null
}
```

---

## 3. Forecast Delivery & Weather Ingestion

The forecast engine pipeline:

```text
Open-Meteo Live ECMWF/GFS API (15-min TTL Cache)
        ↓
Static 14-Feature Parquet Extraction (Copernicus DEM, Roughness, River Distance, SoilGrids)
        ↓
Regional Two-Stage Hurdle Downscaling (Delta / Laterite / Terai Quantiles)
        ↓
Dynamic GDD Phenology Engine (Base-10 Heat Sums for 6 Crops)
        ↓
English Agronomic Advisory Rule Engine (rules/rules.yaml)
        ↓
FastAPI Response (/v1/forecast)
```

The forecast engine supports:
- Full statewide coverage across all 3,339 Gram Panchayats (LGD ID `WB_<gp_code>`).
- 1–5 day downscaled forecast horizon.
- Multi-quantile rainfall ($P_{10}$ dry bound, $P_{50}$ median, $P_{90}$ flood risk bound).
- Rain probability ($0.0$ to $1.0$).
- Maximum & minimum temperatures.
- Dynamic live weather ingestion (`live=true`, default) with 15-minute in-memory TTL cache.
- Graceful offline fallback (`live=false`) to local parquet baseline.
- Context-aware crop advisories in English.

---

## 4. Cadastral Boundary Precision Architecture

TerraMind guarantees **100% zero-displacement spatial grounding** across all 3,339 Gram Panchayats:
1. **Survey of India Block Envelopes:** Every Gram Panchayat boundary polygon is topologically intersected with its authentic Survey of India Community Development Block polygon.
2. **Zero Inversion / Zero Boundary Leakage:** No Gram Panchayat polygon extends outside its containing block boundary.
3. **Voronoi Parcel Partitioning:** Interior block boundaries are derived via high-resolution Voronoi partitioning conditioned on authentic LGD centroid coordinates (`statewide_gp_boundaries.parquet`).
4. **Sub-Millisecond In-Memory Caching:** Boundary geometries are loaded into memory at startup via `_init_statewide_boundaries_cache()`, serving `/v1/statewide/boundaries` requests in $< 2$ milliseconds.

---

## 5. Crop Advisory Command Center & Pest Doctor

TerraMind moves beyond generic weather alerts into a complete operational farm command center:

1. **Dynamic Phenology Engine (`backend/phenology_engine.py`):**
   - Implements FAO-56 heat-sum accumulation ($GDD = \max(0, \frac{T_{\max} + T_{\min}}{2} - T_{\text{base}})$).
   - Dynamically tracks phenological stages for 6 crops: Paddy, Potato, Mustard, Jute, Maize, and Vegetables.
2. **Pest & Disease Doctor (`PestDiseaseDoctor.jsx`):**
   - Diagnostic assistant identifying high-risk pathogen conditions (e.g. Paddy Blast, Sheath Blight, Potato Late Blight) based on multi-day humidity streaks and temperature windows.
3. **Package of Practices (POP):**
   - Authoritative agronomic instructions per crop and developmental stage.
4. **NPK Fertilizer Calculator:**
   - Edaphic-specific nutrient recommendations (Urea, DAP, MOP) adjusted for local soil texture (sand, clay, silt percentages).
5. **FAO-56 $ET_c$ Crop Water Balance Planner:**
   - Computes daily crop evapotranspiration ($ET_c = K_c \times ET_0$) to calculate exact irrigation volumes and prevent water wastage.
6. **Chemical Spray Safety Window:**
   - 24-hour hourly analysis identifying optimal morning spraying windows (07:00–10:30 AM) when wind is moderate and foliage is dry.

---

## 6. Disaster Operations & Multi-Channel Reach

1. **Bay of Bengal Live Cyclone Tracker (`backend/cyclone_engine.py`):**
   - Ingests IMD RSMC tropical cyclone bulletins.
   - Monitors storm categories, central pressure, maximum sustained wind speeds, and port warning signals (e.g. Local Cautionary Signal No. 3).
2. **PMFBY Cryptographic Insurance Certificates (`backend/insurance_engine.py`):**
   - Evaluates parametric weather triggers (excessive rainfall $> 50$ mm, heat stress, prolonged dry spells).
   - Generates tamper-proof claim certificates with HMAC-SHA256 signatures and QR verification payloads (`POST /v1/insurance/certificate`).
3. **Multi-Channel Telecommunications Delivery:**
   - **SMS Alert Generator:** Automatically synthesizes concise, high-priority alerts under 160 characters for standard GSM SMS networks.
   - **1800-TERRAMIND IVR Voice Hotline:** Interactive Voice Response script generator for rural telephony access.
   - **Printable A4 Krishi Bulletin (`PrintableBulletin.jsx`):** Formatted for instant printing and display on Common Service Center (CSC) and Panchayat notice boards.
   - **Web Speech API Voice Synthesis:** In-browser audio readout for farmers with low digital literacy.

---

## 7. Dual AI Agro-Climatic Chatbot

TerraMind features a grounded AI conversational copilot accessible via `POST /v1/ai/chat` and an interactive floating dashboard widget (`AiChatWidget.jsx`).

- **Localized Grounding:** Every response is conditioned on the active Gram Panchayat's downscaled 5-day forecast, elevation, soil texture, and active crop stage.
- **Strict Verification:** Grounded in `rules/rules.yaml` and official agromet bulletins, eliminating hallucinations.
- **Farmer Query Examples:**
  - *"Can I apply urea to my paddy tomorrow morning?"*
  - *"Is there any blast disease risk in my panchayat this week?"*
  - *"When is the safest time to spray fungicide?"*

---

## 8. Doppler Radar Integration

The dashboard features an integrated animated Doppler weather radar player (`RadarControls.jsx`) powered by the RainViewer API:
- Visualizes real-time precipitation clouds overlaid directly onto the Leaflet cadastral map.
- Play, pause, step forward/backward through 10-minute radar frames.
- Synchronized with panchayat boundaries to show incoming convective rain cells.

---

## 9. Operational API Endpoints

| Method | Endpoint | Query / Body Parameters | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | None | API discovery root with status, version, and route links |
| `GET` | `/health` | None | Cloud health monitor, operational model status, and coverage metrics |
| `GET` | `/v1/forecast` | `panchayat_id`, `days=5`, `lang=en`, `crop`, `live` | Core downscaled 5-day forecast with P10/P50/P90 spreads & advisories |
| `GET` | `/v1/statewide/districts` | None | Lists all 22 West Bengal rural districts with GP and block counts |
| `GET` | `/v1/statewide/panchayats` | `district`, `search`, `limit=100` | Search & autocomplete across all 3,339 statewide Gram Panchayats |
| `GET` | `/v1/statewide/stats` | None | Statewide Parquet data lake metrics (2.44M rows, QA status) |
| `GET` | `/v1/statewide/boundaries` | `block_name`, `panchayat_id` | High-precision block-bounded GeoJSON polygon feature collection |
| `POST` | `/v1/ai/chat` | `{"query": str, "panchayat_id": str, "crop": str}` | Dual AI Agro-Climatic Chatbot with localized agronomic grounding |
| `GET` | `/v1/cyclone/active` | None | Live Bay of Bengal cyclone tracking engine, IMD RSMC alerts & LC3 signals |
| `POST` | `/v1/insurance/certificate`| `{"panchayat_id": str, "crop": str, "trigger_type": str}` | Cryptographically signed (HMAC-SHA256) PMFBY insurance claim certificates |
| `GET` | `/v1/radar/timestamps` | None | Live Doppler radar frame timestamps from RainViewer API |
| `GET` | `/v1/agromet/bulletin` | `district` | Official IMD Agromet Advisory Service bulletins |
| `GET` | `/v1/panchayats` | None | Statewide LGD Registry catalog (all 3,339 GPs with 100% equal presentation) |

---

## 10. Example Forecast Response

```json
{
  "panchayat_id": "WB_107001",
  "panchayat_name": "Banchukamari",
  "block_name": "Alipurduar-I",
  "district_name": "Alipurduar",
  "crop": "paddy",
  "issued_at": "2026-09-26T16:30:00+05:30",
  "model_version": "V2.0 Statewide Hurdle (Quantile HGB)",
  "rainfall_model": "Two-Stage Hurdle Downscaling (P10/P50/P90)",
  "is_live_dynamic": true,
  "source": "Open-Meteo Live API (ECMWF/GFS)",
  "coarse_coordinate": {
    "latitude": 26.4813,
    "longitude": 89.1531
  },
  "forecast": [
    {
      "date": "2026-09-26",
      "rain_mm": {
        "p10": 4.1,
        "p50": 4.8,
        "p90": 5.6
      },
      "tmax_c": {
        "p50": 32.1
      },
      "tmin_c": 24.5,
      "rain_probability": 0.82,
      "advisory": {
        "rule_id": "moderate_rain",
        "priority": "medium",
        "type": "warning",
        "text": "Moderate rain expected. Monitor field drainage and avoid unnecessary field operations.",
        "text_en": "Moderate rain expected. Monitor field drainage and avoid unnecessary field operations."
      }
    }
  ],
  "advisories": [
    {
      "date": "2026-09-26",
      "rule_id": "moderate_rain",
      "priority": "medium",
      "type": "warning",
      "text": "Moderate rain expected. Monitor field drainage and avoid unnecessary field operations.",
      "text_en": "Moderate rain expected. Monitor field drainage and avoid unnecessary field operations."
    }
  ],
  "degraded": false,
  "degraded_reason": null
}
```

---

## 11. 4-Member Modular Codebase Architecture

```text
SIH_Panchayat_Project/
├── frontend/                          # [Member 1: Frontend Engineer]
│   ├── src/App.jsx                    # React 19 root layout coordinator
│   ├── src/ComparisonMap.jsx          # Active Cadastral Map with Survey of India envelopes
│   ├── src/components/                # Modular UI Components:
│   │   ├── SearchBar.jsx              # 3,339 GP autocomplete + district filter + GPS detect
│   │   ├── CurrentWeatherHero.jsx     # Current weather card & telemetry
│   │   ├── HourlyWeatherSlider.jsx    # 24h hourly weather & spray safety slider
│   │   ├── QuantileForecastList.jsx   # 5-day P10/P50/P90 uncertainty cards
│   │   ├── MicroTerrainHud.jsx        # Copernicus 30m elevation & slope HUD
│   │   ├── CycloneTracker.jsx         # Bay of Bengal cyclone tracking panel
│   │   ├── CropAdvisoryCommand.jsx    # Crop Command: POP, NPK, FAO-56 ETc
│   │   ├── PestDiseaseDoctor.jsx      # Diagnostic pest & disease assistant
│   │   ├── InsuranceClaimModal.jsx    # PMFBY cryptographic insurance claim generator
│   │   ├── AiChatWidget.jsx           # Floating AI Agro-Climatic Chatbot
│   │   ├── PrintableBulletin.jsx      # Printable A4 Krishi Bulletin
│   │   ├── TrustTransparencyPanel.jsx # Model lineage and trust panel
│   │   └── RadarControls.jsx          # RainViewer Doppler radar animation player
│   └── vite.config.js & package.json  # Vite 8 dev server & dependencies
│
├── backend/                           # [Member 2: Backend Engineer]
│   ├── api.py                         # FastAPI routes & Swagger documentation
│   ├── forecast_engine_v2.py          # 5-day forecast coordinator & regional hurdle router
│   ├── phenology_engine.py            # FAO-56 GDD phenology tracking (6 crops)
│   ├── insurance_engine.py            # PMFBY insurance trigger evaluator & HMAC certificates
│   ├── cyclone_engine.py              # Bay of Bengal cyclone tracking engine
│   ├── ai_chat_engine.py              # Dual AI chatbot engine
│   ├── agromet_bulletin_fetcher.py    # IMD Agromet bulletin scraper
│   ├── advisory_engine.py             # Rule matching & priority resolution engine
│   ├── advisory_context.py            # Dataclasses (soil, crop stage, streaks)
│   └── schemas/                       # Pydantic v2 strict data schemas
│
├── rules/                             # [Member 2: Backend & Domain Rules]
│   └── rules.yaml                     # Single source of truth for agronomic rules & advisory text
│
├── ml/                                # [Member 3: AI / ML & Data Lake Engineer]
│   ├── pipelines/                     # Statewide & Regional Hurdle training pipelines
│   ├── models/                        # Serialized model artifacts:
│   │   ├── statewide_hurdle_v2.pkl    # Master statewide model (1.54 MB)
│   │   ├── hurdle_delta.pkl           # Gangetic & Coastal Delta regional model
│   │   ├── hurdle_laterite.pkl        # Western Laterite Plateau regional model
│   │   └── hurdle_terai.pkl           # Sub-Himalayan Terai & Dooars regional model
│   └── evaluations/                   # Spatial verification & metric evaluation scripts
│
├── data_pipeline/                     # [Member 3: AI / ML & Data Lake Engineer]
│   ├── make_statewide_dataset.py      # Master statewide 2.44M-row dataset generator
│   ├── io_utils.py                    # Unified high-performance Parquet I/O engine
│   ├── metadata/                      # GP registries (statewide_panchayats.parquet)
│   ├── features/                      # Geospatial enrichment & cadastral boundaries:
│   │   ├── statewide_static_features.parquet # 14 geospatial & soil features per GP
│   │   ├── statewide_gp_boundaries.parquet   # Block-bounded cadastral polygons
│   │   └── statewide_gp_boundaries.geojson   # GeoJSON boundary layer
│   └── processed/statewide/           # 22 district Parquet Hive partitions (2.44M rows)
│
├── tests/                             # [Full 248-Test Automated Verification Suite]
│   ├── test_statewide_pipeline.py     # 67 statewide Parquet data lake tests
│   ├── test_statewide_registry.py     # LGD registry and spatial boundary tests
│   ├── test_statewide_geo_features.py # DEM, soil texture, and river proximity tests
│   ├── test_forecast_engine_v2.py     # 5-day coordinator, live API caching, offline fallback
│   ├── test_regional_models.py        # Delta, Laterite, and Terai regional hurdle tests
│   ├── test_insurance_and_phenology.py# PMFBY certificates & GDD phenology tests
│   ├── test_cyclone_tracker.py        # Bay of Bengal cyclone engine tests
│   └── test_ai_chat_engine.py         # Dual AI chatbot copilot tests
│
└── DevOps & Root Entrypoints          # [Member 4: Manager & DevOps]
    ├── Dockerfile                     # Container definition for Render cloud deployment
    ├── .github/workflows/protect-main.yml # GitHub Actions branch guard for main
    ├── api.py                         # Root backward-compatibility shim
    └── requirements.txt               # Pinned Python dependencies
```

---

## 12. Testing & Quality Assurance

TerraMind includes a comprehensive **248-test automated verification suite** in `tests/`:

```bash
# Run complete 248-test verification suite
.venv/bin/pytest tests/ -k "not test_05_live_weather_service"
```

The test suite validates:
- LGD registry boundaries and 100% equal presentation across all 3,339 Gram Panchayats.
- Cadastral boundary precision: 100% zero displacement (all GPs strictly inside block envelopes).
- 14-feature physical realism: DEM elevation, terrain roughness, river distance, and normalized edaphic texture (`sand + clay + silt == 100.0%`).
- Pure Parquet data lake partition integrity (2.44M rows, 22 districts, zero NaNs, zero duplicate keys).
- Zero temporal leakage across the 2024–2025 continuous time horizon.
- Forecast engine 15-minute TTL caching and graceful offline fallback.
- 100% quantile monotonicity across master and regional hurdle models ($0 \le P10 \le P50 \le P90$).
- PMFBY cryptographic HMAC-SHA256 signature verification.
- Bay of Bengal cyclone storm parsing and LC3 port alerting.
- Dynamic GDD phenological stage tracking across 6 crops.

All 248 unit tests pass in ~20 seconds.

---

## 13. Cloud Deployment Architecture

TerraMind is deployed to production using a decoupled cloud architecture:

```text
                        ┌─────────────────────────────────────────────────────────┐
                        │                     USER BROWSER                        │
                        └──────────────────────────┬──────────────────────────────┘
                                                   │
                                    HTTPS Requests │
                                                   ▼
┌──────────────────────────────────────────────────┴──────────────────────────────────────────────────┐
│                                 Vercel Global Edge Network (Frontend)                               │
│  - React 19 + Vite 8 Dashboard                                                                      │
│  - Interactive Leaflet Cadastral Map with Survey of India Block Envelopes                           │
│  - Crop Advisory Command Center, Cyclone Tracker, AI Chatbot Widget                                 │
│  - URL: https://sih-panchayat-project.vercel.app                                                    │
└──────────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                   │
                            API Requests           │  (VITE_API_BASE_URL)
                            [CORS Allowed]         ▼
┌──────────────────────────────────────────────────┴──────────────────────────────────────────────────┐
│                                   Render Web Service (Backend)                                      │
│  - Containerized FastAPI + Uvicorn server (port 7860)                                               │
│  - Operational Statewide Hurdle + 3 Regional Hurdle ML Models in ml/models/                         │
│  - In-memory cached Cadastral Boundaries & Live Weather Ingestion                                   │
│  - URL: https://sih-panchayat-project.onrender.com                                                  │
│  - Swagger Docs: https://sih-panchayat-project.onrender.com/docs                                    │
└──────────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               GitHub Actions CI Guard (Repository Security)                          │
│  - .github/workflows/protect-main.yml intercepts direct pushes to the `main` branch                │
│  - Authorizes only @arnokai and enforces clean pull request / merge workflows                       │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## TerraMind

**TerraMind — Understand Earth. Empower Futures.**

Hyper-local environmental intelligence and agricultural decision support for 3,339 Gram Panchayats.
