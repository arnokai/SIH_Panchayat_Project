# TerraMind Backend Engineering TODO & Milestone Tracker

> **Assigned Owner:** Member 2 — Backend Engineer  
> **Workspaces:** `backend/` and `rules/`  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Status:** Phase 1, Phase 2, and Statewide Parquet Data Lake Milestones COMPLETED.

---

## 1. Milestone Progress Overview

| Phase | Milestone Description | Status | Key Deliverable |
| :--- | :--- | :---: | :--- |
| **Phase 1** | Dynamic Weather Ingestion & Caching | ✅ COMPLETED | Open-Meteo ECMWF/GFS ingestion, 15-min in-memory TTL, offline Parquet fallback |
| **Phase 2** | Statewide ML Downscaling & Quantile Uncertainty | ✅ COMPLETED | Two-Stage Hurdle model (`statewide_hurdle_v2.pkl`), P10/P50/P90 spreads, `degraded: false` |
| **Statewide** | Statewide Registry & Data Lake Integration | ✅ COMPLETED | Endpoints for 3,339 Panchayats across 22 districts; pure Parquet storage |
| **Phase 3** | Agricultural Intelligence & Advisory Rules | 🔄 IN PROGRESS | 10 rules active (`rules.yaml`); multi-crop expansion in progress |
| **Phase 4** | Multi-Channel Delivery Endpoints | 📋 ROADMAP | WhatsApp bulletin, TTS voice audio, printable PDF |
| **Phase 5** | Spatial Administration & Disaster Risk | 🔄 IN PROGRESS | Statewide district & GP discovery complete; flood risk scoring in roadmap |
| **Phase 6** | Schemas, CORS & Automated Testing | 🔄 IN PROGRESS | CORS & 157 unit tests complete; Pydantic v2 schemas in active backlog |

---

## 2. Completed Milestones

### Phase 1: Live Weather Ingestion & Dynamic Caching
- [x] **1.1 Dynamic Open-Meteo Ingestion Service (`backend/forecast_engine_v2.py:fetch_live_block_weather`):**
  - Connects to Open-Meteo operational ECMWF / GFS ensemble blend.
  - Ingests daily precipitation sum, precipitation probability, max/min 2m temperature, and centroid coordinates.
  - Controlled by the `live` query parameter on `GET /v1/forecast` (default: `true`).
- [x] **1.2 In-Memory TTL Cache & Offline Degradation Handling:**
  - Implemented thread-safe in-memory cache `_LIVE_WEATHER_CACHE` with a 15-minute TTL (`_LIVE_WEATHER_TTL_SECONDS = 900`).
  - Cache key: `(round(lat, 4), round(lon, 4), days)`.
  - Graceful degradation: If Open-Meteo call times out (> 3.5s) or fails, seamlessly falls back to offline coarse Parquet forecast (`data_pipeline/raw/coarse_block_forecast.parquet`).

### Phase 2: Statewide ML Downscaling & Quantile Uncertainty Serving
- [x] **2.1 Operational ML Model & Static Feature Loading:**
  - Loads Two-Stage Hurdle model artifact (`ml/models/statewide_hurdle_v2.pkl`) via `joblib`.
  - Pre-loads static geospatial features for all 3,339 Gram Panchayats (`data_pipeline/features/statewide_static_features.parquet`).
- [x] **2.2 Real-Time Downscaling Pipeline:**
  - Constructs 14-element feature vector per GP (DEM elevation, slope, aspect sin/cos, terrain roughness, relative elevation, river distance, sand/clay/silt percentages, DOY sinusoids).
  - Evaluates two-stage hurdle inference: rain occurrence classifier (threshold: 0.35) followed by quantile regressors.
- [x] **2.3 Monotonic Quantile Uncertainty Bounds (P10, P50, P90):**
  - Generates calibrated multi-quantile predictions satisfying strict physical monotonicity: `0.0 <= P10 <= P50 <= P90`.
  - Populates structured `rain_mm` dictionary: `{"p10": float, "p50": float, "p90": float}`.
- [x] **2.4 Lift Degraded Mode:**
  - Response flag transitions to `degraded: false` and `degraded_reason: null` when model inference succeeds.
  - Exposes operational status on `GET /health` and `GET /v1/forecast`.

### Statewide Data Lake & Administrative Endpoints
- [x] **Statewide Registry Resolution (`resolve_panchayat_meta`):**
  - Resolves pilot IDs (`A1`–`A8`), LGD aliases (`WB_107777`–`WB_107784`), and all statewide LGD codes (`WB_107001`–`WB_111115` / numeric `gp_code`).
  - In-memory registry cache `_STATEWIDE_REGISTRY` indexed from `data_pipeline/metadata/statewide_panchayats.parquet`.
- [x] **`GET /v1/statewide/districts`:**
  - Returns aggregated list of all 22 West Bengal rural districts with GP and block counts.
- [x] **`GET /v1/statewide/panchayats`:**
  - Supports instant search and autocomplete across 3,339 Panchayats with `district`, `search`, and `limit` filtering.
- [x] **`GET /v1/statewide/stats`:**
  - Returns metadata metrics for the 2.44M-row data lake and automated QA status from `data_pipeline/reports/statewide_qa_report.md`.
- [x] **Pure Apache Parquet Data Migration:**
  - All active backend loaders migrated to pure Parquet format; zero active CSV dependencies.

### Advisory Rules Engine Core
- [x] **10 Declarative Agricultural Rules (`rules/rules.yaml`):**
  - Core handbook scenarios: `no_spray_rain` (>20 mm), `heat_stress` (>38°C during flowering), `blast_disease_risk` (humidity >85% for 3 days), `sandy_soil_dry_spell` (dry days ≥7 on sandy soil), `harvest_rain` (rain >0 during harvest).
  - Operational extensions: `moderate_rain`, `light_rain`, `dry_day`, `chemical_spray_safe_window` (07:00–10:30 AM spray window), and `sheath_blight_risk`.

### Phase 6 (Completed Components): Security & Testing
- [x] **Production CORS Middleware:**
  - Enabled open CORS middleware in `backend/api.py` allowing cross-origin web and mobile client access.
- [x] **Automated Integration Test Suite:**
  - 157 unit tests passing cleanly across backend engines, statewide data pipeline, feature engineering, and registry resolution (`.venv/bin/python -m unittest discover -s tests`).

---

## 3. Active Priorities (Current Sprint)

### Priority 1: Multi-Crop Phenology Expansion (`data_pipeline/metadata/crop_calendar.yaml`)
- [x] **Multi-Crop Growth Stages:**
  - Expanded beyond existing `paddy` and generic `vegetables` to support distinct Bengal cropping seasons:
    - **Aman Paddy (Kharif):** Tillering (Jul–Sep), Flowering (Sep–Oct), Harvest (Nov–Dec).
    - **Mustard (Rabi oilseed):** Sowing (Oct–Nov), Vegetative (Nov–Dec), Pod formation (Dec–Jan), Harvest (Feb).
    - **Potato (Hooghly/Burdwan belt):** Planting (Oct–Nov), Tuber Bulking (Nov–Jan), Harvest (Jan–Feb).
    - **Jute (Pre-Kharif fiber):** Sowing (Mar–Apr), Vegetative (May–Jun), Harvest/Retting (Jul–Aug).
    - **Vegetables (Horticulture):** Year-round continuous vegetative and fruiting management.
- [x] **Context Builder Integration:**
  - Updated `data_pipeline/metadata/crop_calendar.py` with dynamic stage iteration and calendar resolution.

### Priority 2: Pest & Disease Rule Expansion (`rules/rules.yaml`)
- [x] **Brown Plant Hopper (BPH) Warning Rule (`paddy_bph_risk`):**
  - Triggers when relative humidity > 80%, temperatures are 28°C–34°C, and dry days ≥ 3 during rice tillering.
- [x] **Potato Late Blight (*Phytophthora infestans*) (`potato_late_blight`):**
  - Triggers during cool, humid conditions (humidity > 82%, tmax between 12°C–25°C) with prophylactic Mancozeb spray guidance.
- [x] **Potato Waterlogging & Drainage (`potato_waterlogging_risk`):**
  - Triggers when rain > 15 mm to avert tuber rot and soil compaction.
- [x] **Mustard Aphid & White Rust Alert (`mustard_aphid_rust_risk`):**
  - Triggers when humidity > 75% and temperatures are 15°C–26°C.
- [x] **Jute Stem Rot & Stagnation Alert (`jute_stem_rot`):**
  - Triggers on heavy rainfall (>20 mm) and high humidity to prevent Macrophomina stem rot.

### Priority 3: Pydantic v2 Schema Migration (`backend/schemas/`)
- [x] **Strict Pydantic v2 Schema Models (`backend/schemas/models.py`):**
  - `RootResponse`, `HealthResponse`, `PanchayatBrief`, `PanchayatListResponse`.
  - `StatewideDistrictsResponse`, `StatewidePanchayatsResponse`, `StatewideStatsResponse`.
  - `QuantileRain`, `TMaxObj`, `AdvisoryDetail`, `AdvisorySummaryItem`, `DailyForecast`.
  - `CurrentWeather`, `HourlyRecord`, `HourlyWeather`, `LiveWeatherPayload`, `ForecastResponse`.
- [x] **FastAPI Route Decorator Binding:**
  - Bound all endpoints with `response_model=...` generating auto-documented interactive Swagger UI at `/docs`.
- [x] **Automated Schema Test Suite (`tests/test_schemas.py`):**
  - Added 6 dedicated unit tests verifying full model validation across all endpoints.

---

## 4. Future Delivery Roadmap

### Phase 4: Multi-Channel Delivery Endpoints (Layer 5)
- [ ] **4.1 WhatsApp Bulletin Formatter (`GET /v1/export/whatsapp`):**
  - Pre-format clean, emoji-formatted text for forwarding to farmer groups.
- [ ] **4.2 Spoken Audio / TTS Streaming Endpoint (`GET /v1/tts/synthesize`):**
  - Stream synthesized audio (`audio/mpeg`) for farmers using neural TTS.
- [ ] **4.3 Printable Krishi Bulletin PDF (`GET /v1/bulletin/pdf`):**
  - Generate an official 1-page A4 PDF bulletin for notice boards.
- [ ] **4.4 SMS Broadcast Message Builder:**
  - 160-character GSM-7/Unicode SMS alerts for severe weather warnings.

### Phase 5: Spatial Administration & Disaster Risk
- [ ] **5.1 Single-Call Block Overview (`GET /v1/block/overview`):**
  - Single batch call returning today's weather and top advisory for all Panchayats in a selected Block.
- [ ] **5.2 Waterlogging & Flood Risk Assessment (`GET /v1/disaster/flood-risk`):**
  - Model surface runoff accumulation from 48-hour rainfall, DEM elevation, and river proximity.
- [ ] **5.3 PMFBY Crop Insurance Damage Export (`GET /v1/reports/damage-assessment`):**
  - Incident verification report for extreme rainfall (>50 mm) or heatwave damage.

### Scientific Validation
- [ ] **KVK Scientist Validation Interface (`GET /v1/rules`, `POST /v1/rules/review`):**
  - Portal for agricultural university / KVK scientists to review rule thresholds and submit feedback.
