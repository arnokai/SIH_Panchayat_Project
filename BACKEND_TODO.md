# TerraMind Backend Workspace & Technical Roadmap

> **Assigned Owner:** Member 2 — Backend Engineer  
> **Workspaces:** `backend/` and `rules/`  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Live API (Render):** [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)  
> **Interactive Swagger Docs:** [https://sih-panchayat-project.onrender.com/docs](https://sih-panchayat-project.onrender.com/docs)  
> **Status:** Operational V2 delivery scaffold active. Degraded fallback mode active pending live downscaling model serving.

---

## 1. Executive Summary & Role Mission

As the **Backend Engineer (Member 2)**, you own the core computational and decision-support engines of TerraMind. You are responsible for:
1. **The Fast & Reliable REST API (`backend/api.py`):** Serving high-throughput, low-latency forecasts and agricultural advisories to the React frontend, mobile PWA, KVK dashboard, and external consumers.
2. **The Agricultural Advisory Rule Engine (`backend/advisory_engine.py` & `rules/rules.yaml`):** Translating raw weather forecasts into actionable, life-saving agronomic instructions in colloquial Bengali and English.
3. **ML Model Serving & Quantile Uncertainty (`backend/forecast_engine_v2.py`):** Integrating trained downscaling models from `ml/models/` into real-time inference, generating P10/P50/P90 uncertainty spreads, and safely managing the fallback degradation state.
4. **Multi-Channel Delivery Endpoints:** Providing WhatsApp bulletin formatting, Bengali Text-to-Speech (TTS) audio streaming, printable PDF notice board sheets, and KVK scientist validation interfaces.

---

## 2. Current Architecture & Codebase Map

### Directory Structure
```text
backend/
├── __init__.py
├── api.py                          # FastAPI application, route handlers, CORS, Swagger docs
├── forecast_engine_v2.py           # 5-day forecast assembly, dry-streak calculation, fallback logic
├── advisory_engine.py              # Rule loader, context matcher, and priority selector
├── advisory_context.py             # AdvisoryContext dataclass and soil context mapping
├── forecast_advisory_context.py    # Merges weather, soil, crop calendar, and streak days
└── README.md                       # (This guide and actionable roadmap)

rules/
└── rules.yaml                      # Declarative agricultural rules, thresholds, English & Bengali text

data/ & data_pipeline/
├── panchayats.csv                  # GPS coordinates & metadata for the 8 Amdanga Panchayats
├── crop_calendar.yaml              # Biological crop growth stages mapped by calendar month
└── raw/
    ├── coarse_block_forecast.csv   # Offline fallback forecast data
    └── panchayat_soil_context.csv  # Soil classifications (SoilGrids) per panchayat
```

### Current Runtime Execution Flow
```text
[HTTP Client / Frontend]
        │
        ▼ GET /v1/forecast?panchayat_id=A2&days=5&lang=bn&crop=paddy
[FastAPI Router (backend/api.py)]
        │
        ▼ Validates params (panchayat_id in A1..A8, days 1..5, lang in bn|en)
[Forecast Engine (backend/forecast_engine_v2.py)]
        │
        ├─► Reads coarse forecast from data_pipeline/raw/coarse_block_forecast.csv
        ├─► Calculates dry streaks (calculate_forecast_dry_days)
        │
        ▼ For each day (1 to 5):
[Forecast Advisory Context (backend/forecast_advisory_context.py)]
        │
        ├─► Reads soil type from panchayat_soil_context.csv
        ├─► Reads crop biological stage from data/crop_calendar.yaml
        ├─► Combines with weather (rain_mm, tmax_c, tmin_c, humidity, streaks)
        │
        ▼ Evaluates against rules:
[Advisory Engine (backend/advisory_engine.py)]
        │
        ├─► Evaluates boolean conditions against context in rules/rules.yaml
        ├─► Ranks matches: critical > high > medium > low > info
        ├─► Selects highest priority advice & extracts text_bn / text_en
        │
        ▼ Returns JSON Response:
[Standardized UTF-8 JSON Response with degraded=True]
```

---

## 3. Gap Analysis: Current State vs. Hackathon Gold Standard

| Feature | Current V2 State | Production / Hackathon Target | Action Required |
| :--- | :--- | :--- | :--- |
| **Forecast Source** | Static CSV (`coarse_block_forecast.csv` from Aug 2024) | Live Open-Meteo / IMD API sync with in-memory caching | Implement live fetcher with 6-hour TTL cache & offline fallback |
| **ML Downscaling** | Degraded mode (`degraded: true`), uses raw coarse forecast | Operational inference using trained XGBoost models | Serve `ml/models/v1_3_*.pkl` on startup; calculate panchayat deltas |
| **Uncertainty Bounds** | Hardcoded `p10: None, p90: None` | Quantile spreads (P10, P50, P90) | Compute probabilistic confidence intervals for rain & temp |
| **Spatial Overview** | Requires 8 separate HTTP calls from frontend | Single `GET /v1/block/overview` endpoint | Batch query returning summary for all 8 panchayats in < 50ms |
| **Agricultural Rules** | 8 basic rules (handbook scenarios) | 18+ comprehensive rules (diseases, sprays, fertilizers, irrigation) | Expand `rules.yaml` with pest models, fertilizer & spray windows |
| **Crop Diversity** | Paddy and generic vegetables | Aman Paddy, Boro Paddy, Mustard, Potato, Jute | Update `crop_calendar.yaml` with multi-crop phenological stages |
| **Delivery APIs** | JSON forecast only | WhatsApp formatter, Bengali Audio TTS, Printable PDF Bulletin | Add endpoints for Layer 5 multi-channel delivery |
| **KVK Validation** | Hardcoded static YAML file | Dynamic validation & threshold review endpoint | Create `/v1/rules` review & feedback endpoints for agri-scientists |
| **Schema Validation** | Loose Python dicts | Strict Pydantic v2 Models | Create `backend/schemas/` for robust validation and Swagger types |
| **Testing** | Rule & context unit tests | Full API integration tests (`TestClient`) | Add `tests/test_api_endpoints.py` testing all routes & edge cases |

---

## 4. Complete Action Plan & Task Checklist

### Phase 1: Live Weather Ingestion & Dynamic Caching
- [ ] **1.1 Build Live Open-Meteo Ingestion Service (`backend/services/weather_service.py`):**
  - Implement async HTTP client using `httpx` or `requests` to fetch 5-day hourly and daily forecasts for Amdanga Block coordinates (`22.7937° N, 88.5204° E`).
  - Extract daily parameters: `precipitation_sum`, `precipitation_probability_max`, `temperature_2m_max`, `temperature_2m_min`, `relative_humidity_2m_mean`, `wind_speed_10m_max`.
- [ ] **1.2 In-Memory / Disk Cache with TTL:**
  - Cache live weather data for 6 hours (matches IMD forecast update cycles).
  - Include graceful degradation: If external API call times out (> 3.5s) or fails, seamlessly serve the latest cached response or fallback to `coarse_block_forecast.csv`.
- [ ] **1.3 Manual / Scheduled Cache Refresh Endpoint:**
  - `POST /v1/admin/forecast/refresh`: Allows manual triggering of fresh weather data pull.

---

### Phase 2: Serving ML Downscaling Models & Quantile Uncertainty
- [ ] **2.1 Load Trained ML Models on Application Startup (`backend/ml_service.py`):**
  - Load `ml/models/v1_3_rain_residual.pkl` and `ml/models/v1_3_rain_calibration.pkl` via `joblib` inside FastAPI's `lifespan` handler.
  - Pre-load static panchayat GIS features: elevation DEM, slope, aspect, distance to water body, soil sand/clay percentages.
- [ ] **2.2 Real-Time Downscaling Pipeline:**
  - Construct feature vector for each panchayat:
    8924\text{Features} = [\text{coarse\_rain}, \text{coarse\_tmax}, \text{elevation}, \text{slope}, \text{dist\_river}, \text{soil\_type}, \dots]8924
  - Run inference: $\text{downscaled\_rain} = \text{calibrate}(\text{coarse\_rain}) + \text{residual\_model.predict}(\mathbf{x})$.
  - Clip outputs to physical bounds ($\ge 0\text{ mm}$).
- [ ] **2.3 Quantile Uncertainty Bounds (P10, P50, P90):**
  - Compute P10 (optimistic/dry bound), P50 (median/expected), and P90 (pessimistic/heavy rain bound).
  - Populate `rain_mm: {"p10": ..., "p50": ..., "p90": ...}` and `tmax_c: {"p10": ..., "p50": ..., "p90": ...}` in API responses.
- [ ] **2.4 Lift Degraded Mode:**
  - Transition response flag to `degraded: false` when downscaled model inference succeeds.
  - Automatically set `degraded: true` with explanatory string if model fails or static fallback is engaged.

---

### Phase 3: Advanced Agricultural Intelligence & Advisory Rule Engine
- [ ] **3.1 Rice Pest & Disease Warning Models:**
  - **Paddy Blast (*Pyricularia oryzae*):** Trigger when relative humidity $> 85\%$ for $\ge 3$ consecutive days with temperatures between 4^\circ\text{C} - 30^\circ\text{C}$.
  - **Sheath Blight:** Trigger when rain $> 15\text{ mm}$ and humidity $> 90\%$ during tillering or panicle initiation stages.
  - **Brown Plant Hopper (BPH):** Trigger during high humidity and dense vegetative canopy with no rain for 4 days.
  - **Potato Late Blight (*Phytophthora infestans*):** Trigger during winter/Rabi when nighttime temp $< 15^\circ\text{C}$ with dense fog/humidity $> 90\%$.
- [ ] **3.2 Actionable Operational Windows:**
  - **Fertilizer / Urea Runoff Lockout:**
    - If forecast rain $> 15\text{ mm}$ in next 48 hours: Alert farmer to delay top-dressing urea to prevent fertilizer leaching.
  - **Pesticide & Fungicide Spray Window:**
    - Calculate exact safe spray hours (e.g., *"Safe to spray between 07:00 AM - 10:30 AM tomorrow. Wind speed < 12 km/h, rain-free for 4+ hours after application"*).
  - **Irrigation Guidance by Soil Type:**
    - Alluvial Clay (high water retention): Advise delayed irrigation if light rain is coming.
    - Sandy Loam (rapid drainage): Alert dry spell risk if `dry_days >= 5`.
- [ ] **3.3 Multi-Crop Phenology Expansion (`data/crop_calendar.yaml`):**
  - Add specific regional crop calendars for Bengal:
    - `aman_paddy`: Nursery (Jun–Jul), Tillering (Aug–Sep), Flowering (Oct), Harvest (Nov–Dec).
    - `boro_paddy`: Sowing (Nov–Dec), Transplanting (Jan), Flowering (Mar), Harvest (Apr–May).
    - `mustard`: Sowing (Oct–Nov), Vegetative (Dec), Pod formation (Jan), Harvest (Feb).
    - `potato`: Planting (Nov), Tuber bulking (Dec–Jan), Harvest (Feb).
    - `jute`: Sowing (Mar–Apr), Vegetative (May–Jun), Harvest/Retting (Jul–Aug).
- [ ] **3.4 KVK Scientist Rule Verification Interface:**
  - `GET /v1/rules`: Return list of active rules, current threshold triggers, and metadata.
  - `POST /v1/rules/review`: Endpoint for KVK agronomists to approve or modify rule thresholds and submit feedback.

---

### Phase 4: Multi-Channel Delivery Endpoints (Layer 5 Architecture)
- [ ] **4.1 WhatsApp Bulletin Formatter (`GET /v1/export/whatsapp`):**
  - Generate clean, emoji-formatted bilingual text ready for one-click forwarding to farmer WhatsApp groups:
    ```text
    🌾 *টেরামাইন্ড পঞ্চায়েত কৃষি পরামর্শ* 🌾
    📍 পঞ্চায়েত: আমডাঙা (A2) | তারিখ: ০৫/০৯/২০২৬
    🌧️ আগামী ৫ দিনের পূর্বাভাস:
    • আজ: হালকা বৃষ্টি (২.৪ মিমি) | সর্বোচ্চ: ৩২°C
    • কাল: শুষ্ক দিন | সর্বোচ্চ: ৩৪°C
    ⚠️ *কৃষি সতর্কতা:*
    ইউরিয়া সার প্রয়োগ করবেন না। আগামী ২৪ ঘণ্টায় ভারী বৃষ্টির সম্ভাবনা রয়েছে।
    🔗 সম্পূর্ণ বুলেটিন দেখুন: https://sih-panchayat-project.vercel.app
    ```
- [ ] **4.2 Spoken Bengali Audio / TTS Endpoint (`GET /v1/tts/synthesize`):**
  - Stream synthesized spoken Bengali audio (`audio/mpeg`) for illiterate farmers using Bhashini, AI4Bharat Indic-TTS, or edge TTS engines.
- [ ] **4.3 Printable Krishi Bulletin PDF (`GET /v1/bulletin/pdf`):**
  - Generate an official 1-page A4 PDF bulletin suitable for printing and displaying on Gram Panchayat and CSC notice boards.
- [ ] **4.4 SMS Broadcast Message Builder:**
  - Provide concise 160-character GSM-7 / Unicode SMS snippets for critical weather warnings (e.g. Kalbaishakhi thunderstorms, extreme heat).

---

### Phase 5: Spatial Administration & Disaster Risk Endpoints
- [ ] **5.1 Single-Call Block Overview (`GET /v1/block/overview`):**
  - Returns today's forecast and highest-priority advisory for all 8 panchayats in a single batch response.
  - Eliminates 8 round-trip requests from the frontend Leaflet map.
- [ ] **5.2 Waterlogging & Flood Risk Assessment (`GET /v1/disaster/flood-risk`):**
  - Calculate surface ponding risk using 48-hour accumulated rainfall, DEM elevation, and proximity to drainage channels.
  - Output risk index: `LOW`, `MODERATE`, `SEVERE`.
- [ ] **5.3 PMFBY Crop Insurance Loss Verification Export (`GET /v1/reports/damage-assessment`):**
  - Export verifiable weather incident reports (excess rain > 50 mm, heatwave > 40°C during flowering) for crop insurance verification.

---

### Phase 6: Code Quality, Schemas, Security & Automated Testing
- [ ] **6.1 Pydantic v2 Schema Migration (`backend/schemas/`):**
  - Define strict models: `ForecastRequest`, `ForecastResponse`, `DailyForecast`, `Advisory`, `UncertaintyRange`, `PanchayatOverview`.
- [ ] **6.2 Production CORS & Rate Limiting:**
  - Configure CORS allow-list for `sih-panchayat-project.vercel.app` and `localhost:5173`.
  - Add rate-limiting (`slowapi`) on forecast and export endpoints to prevent abuse.
- [ ] **6.3 Integration Test Suite (`tests/test_api_endpoints.py`):**
  - Implement full pytest suite testing:
    - Valid query parameters for all 8 panchayats.
    - Parameter validation errors (404 for invalid panchayat, 422 for invalid crop/lang).
    - Response latency benchmarks (< 80 ms).
    - Consistency between English and Bengali outputs.

---

## 5. API Endpoints Specification Table

| Method | Endpoint | Query / Body Parameters | Response | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | None | `{status: "ok", degraded: bool, ...}` | Cloud health check & degradation monitor |
| `GET` | `/v1/panchayats` | None | `{count: 8, panchayats: [...]}` | List 8 Amdanga Panchayats with names & IDs |
| `GET` | `/v1/forecast` | `panchayat_id` (req), `days` (1-5), `lang` (bn/en), `crop` | Standardized 5-day forecast + advisories | Core forecast delivery for UI cards |
| `GET` | `/v1/block/overview` | `days` (default: 1), `lang` (bn/en) | `{block: "Amdanga", panchayats: [...]}` | Batch summary powering Leaflet map in 1 call |
| `GET` | `/v1/export/whatsapp` | `panchayat_id` (req), `lang` (bn/en) | `{text: "...", encoded_url: "..."}` | Pre-formatted text for WhatsApp forwarding |
| `GET` | `/v1/tts/synthesize` | `panchayat_id` (req), `lang` (default: bn) | Audio stream (`audio/mpeg`) | Voice advisory for illiterate farmers |
| `GET` | `/v1/bulletin/pdf` | `panchayat_id` (req) | PDF stream (`application/pdf`) | Printable 1-page notice-board bulletin |
| `GET` | `/v1/rules` | `crop` (opt), `priority` (opt) | `{count: ..., rules: [...]}` | List all active advisory rules |
| `POST` | `/v1/rules/review` | `{rule_id: str, scientist_name: str, ...}` | `{status: "recorded"}` | KVK scientist advisory validation portal |
| `GET` | `/v1/disaster/flood-risk` | `panchayat_id` (opt) | `{panchayat_id: ..., flood_risk: "MODERATE"}` | Elevation + rain accumulation flood warning |
| `POST` | `/v1/admin/forecast/refresh` | API Key header | `{refreshed_at: ..., status: "success"}` | Trigger live weather sync & cache update |

---

## 6. Target Data Contracts & Response Schema

### `GET /v1/forecast` Example Response
```json
{
  "panchayat_id": "A2",
  "panchayat_name": "AMDANGA",
  "crop": "paddy",
  "issued_at": "2026-09-05T06:00:00+05:30",
  "model_version": "V2.1-Operational-XGBoost",
  "rainfall_model": "Two-Stage Residual Hurdle + Quantile Regressor",
  "source": "Open-Meteo Live / IMD Grid Blend",
  "coarse_coordinate": {
    "latitude": 22.7937,
    "longitude": 88.5204
  },
  "forecast": [
    {
      "date": "2026-09-05",
      "rain_mm": {
        "p10": 1.2,
        "p50": 3.4,
        "p90": 8.1
      },
      "tmax_c": {
        "p10": 31.5,
        "p50": 33.2,
        "p90": 34.8
      },
      "tmin_c": 26.4,
      "rain_probability": 0.45,
      "humidity_percent": 82,
      "wind_speed_kmh": 11.2,
      "advisory": {
        "rule_id": "light_rain",
        "priority": "low",
        "type": "success",
        "text": "হালকা বৃষ্টি। সার প্রয়োগ করা নিরাপদ.",
        "text_en": "Light rain. Safe to apply light fertilisers.",
        "text_bn": "হালকা বৃষ্টি। সার প্রয়োগ করা নিরাপদ."
      }
    }
  ],
  "advisories": [
    {
      "date": "2026-09-05",
      "rule_id": "light_rain",
      "priority": "low",
      "type": "success",
      "text_en": "Light rain. Safe to apply light fertilisers.",
      "text_bn": "হালকা বৃষ্টি। সার প্রয়োগ করা নিরাপদ."
    }
  ],
  "degraded": false,
  "degraded_reason": null
}
```

---

## 7. Developer Cheatsheet & Workflow

### Start Backend Locally
```bash
# In project root:
source .venv/bin/activate
uvicorn backend.api:app --reload --port 8000
```
Open interactive docs: **http://127.0.0.1:8000/docs**

### Run Backend Integration Tests
```bash
pytest tests/ -v
```

### Git Branching Rules for Backend
1. Always work in a dedicated branch:
   ```bash
   git checkout -b feature/backend-<feature-name>
   ```
2. Restrict your edits to `backend/`, `rules/`, and backend test files in `tests/`.
3. Do not modify `frontend/` or `ml/` without coordinating with Member 1 or Member 3.
4. Ensure all tests pass before opening a Pull Request into `main`.
