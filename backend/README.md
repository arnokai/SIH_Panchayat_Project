# TerraMind Backend Workspace & Technical Architecture

> **Assigned Owner:** Member 2 — Backend Engineer  
> **Workspaces:** `backend/` and `rules/`  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Live API (Render):** [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)  
> **Interactive Swagger Docs:** [https://sih-panchayat-project.onrender.com/docs](https://sih-panchayat-project.onrender.com/docs)  
> **Status:** Operational V2 Statewide Architecture Active. Pure Apache Parquet storage, dynamic Open-Meteo ingestion with 15-minute in-memory caching, and Two-Stage Hurdle model serving across all 3,339 Gram Panchayats (`degraded: false`).

---

## 1. Executive Summary & Role Mission

As the **Backend Engineer (Member 2)**, you own the computational and decision-support engines of TerraMind. You are responsible for:
1. **The Fast & Reliable REST API (`backend/api.py`):** Serving high-throughput, low-latency forecasts and agricultural advisories to the React frontend, mobile PWA, KVK dashboard, and external consumers.
2. **The Agricultural Advisory Rule Engine (`backend/advisory_engine.py` & `rules/rules.yaml`):** Translating raw weather forecasts into actionable, life-saving agronomic instructions in clear English.
3. **ML Model Serving & Quantile Uncertainty (`backend/forecast_engine_v2.py`):** Integrating trained downscaling models from `ml/models/statewide_hurdle_v2.pkl` into real-time inference, generating P10/P50/P90 uncertainty spreads, and safely managing fallback state.
4. **Dynamic Weather Ingestion:** Fetching real-time 5-day forecasts via Open-Meteo ECMWF/GFS models with in-memory TTL caching and offline Parquet fallback.
5. **Statewide Data Lake Integration:** Querying the pure Apache Parquet data lake covering all 3,339 Gram Panchayats across all 22 rural districts of West Bengal.

---

## 2. Architecture & Codebase Map

### Directory Structure
```text
backend/
├── __init__.py
├── api.py                          # FastAPI application, route handlers, CORS, Swagger docs
├── forecast_engine_v2.py           # 5-day forecast assembly, dynamic Open-Meteo fetcher, ML hurdle serving
├── advisory_engine.py              # Rule loader, context matcher, and priority selector
├── advisory_context.py             # AdvisoryContext dataclass and soil context mapping
├── forecast_advisory_context.py    # Merges weather, soil, crop calendar, and dry-streak days
└── README.md                       # Backend workspace guide and API reference

rules/
└── rules.yaml                      # Declarative agricultural rules (10 rules), thresholds, English text

data_pipeline/
├── metadata/
│   ├── statewide_panchayats.parquet # Official catalog of 3,339 West Bengal Gram Panchayats
│   ├── crop_calendar.yaml          # Biological crop growth stages mapped by calendar month
│   └── crop_calendar.py            # Phenological context lookup helper
├── features/
│   └── statewide_static_features.parquet # 14 geospatial & soil features per GP (3,339 rows)
├── raw/
│   ├── coarse_block_forecast.parquet     # Offline fallback forecast dataset
│   ├── panchayat_soil_context.parquet    # Soil classifications (SoilGrids) per panchayat
│   ├── advisory_context_history.parquet  # Historical dry-streak and context records
│   └── panchayat_coordinates.parquet     # Centroid coordinate reference
└── processed/
    └── statewide/
        └── district_name=*/              # Partitioned Parquet data lake (2.44M rows, 22 districts)
```

### Runtime Execution Flow
```text
[HTTP Client / Frontend]
        │
        ▼ GET /v1/forecast?panchayat_id=WB_107001&days=5&lang=bn&crop=paddy&live=true
[FastAPI Router (backend/api.py)]
        │
        ▼ Validates params (panchayat_id in statewide catalog, days 1..5, lang in bn|en, crop)
[Forecast Engine (backend/forecast_engine_v2.py)]
        │
        ├─► Resolves metadata via resolve_panchayat_meta (lat, lon, block, district)
        │
        ├─► Dynamic Weather Fetch (live=True):
        │   ├─► Checks in-memory cache _LIVE_WEATHER_CACHE (15-min TTL)
        │   ├─► If cache miss: GET api.open-meteo.com/v1/forecast (ECMWF/GFS daily parameters)
        │   └─► If timeout (>3.5s) / error: Fallback to coarse_block_forecast.parquet
        │
        ├─► Loads ML Hurdle Model (ml/models/statewide_hurdle_v2.pkl)
        ├─► Loads Static GIS Features (statewide_static_features.parquet for target GP)
        │
        ▼ For each forecast day (1 to 5):
[Two-Stage Hurdle ML Downscaling]
        ├─► Stage 1: Rain occurrence classifier (probability threshold: 0.35)
        ├─► Stage 2: Quantile regressors (P10, P50, P90 with monotonicity 0 <= P10 <= P50 <= P90)
        │
[Forecast Advisory Context (backend/forecast_advisory_context.py)]
        ├─► Resolves soil context & dry streaks (calculate_forecast_dry_days)
        ├─► Evaluates crop phenological stage from crop_calendar.yaml
        │
[Advisory Engine (backend/advisory_engine.py)]
        ├─► Evaluates boolean conditions against context in rules/rules.yaml (10 rules)
        ├─► Ranks matches: high > medium > low > info
        ├─► Selects highest priority advice & extracts text_en
        │
        ▼ Returns UTF-8 JSON Response:
[Standardized Response: degraded=false, is_live_dynamic=true/false]
```

---

## 3. Operational API Endpoints Specification

### Active Endpoints Summary

| Method | Endpoint | Query Parameters | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | None | API discovery root with status, version, and route links |
| `GET` | `/health` | None | Cloud health monitor, operational model status, and coverage metrics |
| `GET` | `/v1/forecast` | `panchayat_id` (req), `days` (1-5), `lang` (en), `crop` (str), `live` (bool) | Core downscaled 5-day forecast with P10/P50/P90 spreads & advisories |
| `GET` | `/v1/statewide/districts` | None | Lists all 22 West Bengal rural districts with GP and block counts |
| `GET` | `/v1/statewide/panchayats` | `district` (opt), `search` (opt), `limit` (default: 100) | Search & autocomplete across 3,339 statewide Gram Panchayats |
| `GET` | `/v1/statewide/stats` | None | Statewide Parquet data lake metrics (2.44M rows, QA status) |
| `GET` | `/v1/panchayats` | None | Returns pilot and canonical LGD alias list (count: 16) |

---

### Detailed Live Endpoint Specifications & Curl Commands

#### 1. `GET /health`
Verifies backend operational health, model loading state, and data lake coverage. When `ml/models/statewide_hurdle_v2.pkl` is loaded, the service reports `degraded: false`.

**Curl Command:**
```bash
curl -s "http://127.0.0.1:8000/health"
```

**Response Example:**
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

#### 2. `GET /v1/forecast`
Primary endpoint serving real-time downscaled weather and agronomic advisories.
- **`panchayat_id`** (`str`, required): Pilot code (`A1`–`A8`), LGD alias (`WB_107777`–`WB_107784`), or statewide LGD ID (`WB_107001`–`WB_111115` / numeric `gp_code`).
- **`days`** (`int`, optional, default: `5`): Forecast horizon from `1` to `5` days.
- **`lang`** (`str`, optional, default: `"en"`): Advisory language: `"en"` (English).
- **`crop`** (`str`, optional, default: `"paddy"`): Target crop for advisory context.
- **`live`** (`bool`, optional, default: `true`): If `true`, fetches dynamic Open-Meteo ECMWF/GFS weather with 15-minute TTL caching; if `false` or upon network timeout (>3.5s), gracefully falls back to offline Parquet forecast data (`coarse_block_forecast.parquet`).

**Curl Command (Live Dynamic Weather):**
```bash
curl -s "http://127.0.0.1:8000/v1/forecast?panchayat_id=WB_107001&days=5&lang=en&crop=paddy&live=true"
```

**Curl Command (English & Offline Fallback):**
```bash
curl -s "http://127.0.0.1:8000/v1/forecast?panchayat_id=WB_107001&days=5&lang=en&crop=paddy&live=false"
```

**Response Example:**
```json
{
  "panchayat_id": "WB_107001",
  "panchayat_name": "Banchukamari",
  "block_name": "Alipurduar-I",
  "district_name": "Alipurduar",
  "crop": "paddy",
  "issued_at": "2026-09-08T22:47:32.123456+05:30",
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
      "date": "2026-09-08",
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
      "date": "2026-09-08",
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

#### 3. `GET /v1/statewide/districts`
Returns statewide district-level aggregation (22 rural districts) with total Gram Panchayat and block counts. Powers frontend district selectors and state dashboards.

**Curl Command:**
```bash
curl -s "http://127.0.0.1:8000/v1/statewide/districts"
```

**Response Example:**
```json
{
  "state": "West Bengal",
  "district_count": 22,
  "total_panchayats": 3339,
  "districts": [
    {
      "district_name": "Alipurduar",
      "total_panchayats": 66,
      "total_blocks": 6
    },
    {
      "district_name": "Bankura",
      "total_panchayats": 190,
      "total_blocks": 22
    }
  ]
}
```

---

#### 4. `GET /v1/statewide/panchayats`
Fast search and autocomplete across all 3,339 Gram Panchayats with query filtering by district, substring search on Panchayat/Block names, and result limit.

**Query Parameters:**
- `district` (`str | None`, optional): Filter by district name (case-insensitive).
- `search` (`str | None`, optional): Substring search against `panchayat_name` or `block_name`.
- `limit` (`int`, optional, default: `100`): Maximum results to return.

**Curl Command:**
```bash
curl -s "http://127.0.0.1:8000/v1/statewide/panchayats?district=Alipurduar&search=ban&limit=5"
```

**Response Example:**
```json
{
  "state": "West Bengal",
  "total_matched": 1,
  "returned": 1,
  "panchayats": [
    {
      "gp_code": 107001,
      "panchayat_id": "WB_107001",
      "panchayat_name": "Banchukamari",
      "block_name": "Alipurduar-I",
      "district_name": "Alipurduar",
      "latitude": 26.48126945,
      "longitude": 89.15314149
    }
  ]
}
```

---

#### 5. `GET /v1/statewide/stats`
Summary statistics and automated QA validation report status for the 2.44M-row data lake.

**Curl Command:**
```bash
curl -s "http://127.0.0.1:8000/v1/statewide/stats"
```

**Response Example:**
```json
{
  "state": "West Bengal",
  "total_rows": 2440809,
  "total_panchayats": 3339,
  "total_blocks": 342,
  "total_districts": 22,
  "date_range": "2024-01-01 to 2025-12-31 (731 continuous days)",
  "qa_status": "PASS",
  "storage_format": "Apache Parquet (District Hive Partitions)",
  "memory_optimization": "Sub-second district loading"
}
```

---

#### 6. `GET /v1/panchayats`
Returns pilot and canonical LGD alias list (16 records: `A1`–`A8` pilot codes and `WB_107777`–`WB_107784` LGD IDs).

**Curl Command:**
```bash
curl -s "http://127.0.0.1:8000/v1/panchayats"
```

**Response Example:**
```json
{
  "count": 16,
  "panchayats": [
    {
      "panchayat_id": "A1",
      "panchayat_name": "ADHATA"
    },
    {
      "panchayat_id": "WB_107777",
      "panchayat_name": "ADHATA"
    }
  ]
}
```

---

#### 7. `GET /`
Service discovery root endpoint.

**Curl Command:**
```bash
curl -s "http://127.0.0.1:8000/"
```

**Response Example:**
```json
{
  "name": "TerraMind Panchayat Forecast API",
  "version": "2.1",
  "status": "online",
  "docs": "/docs",
  "health": "/health",
  "panchayat_endpoint": "/v1/panchayats",
  "forecast_endpoint": "/v1/forecast"
}
```

---

### Future / Planned Endpoints (Roadmap)

The following endpoints were proposed during initial architectural planning and remain on the future delivery roadmap (tracked in `docs/roadmap/BACKEND_TODO.md`). Note that client-side implementations currently provide instant WhatsApp sharing and voice synthesis in the frontend:

| Endpoint | Method | Roadmap Phase | Description / Current Workaround |
| :--- | :--- | :--- | :--- |
| `/v1/block/overview` | `GET` | Phase 5 | Batch block summary. (Current: frontend queries `/v1/forecast` per GP). |
| `/v1/export/whatsapp` | `GET` | Phase 4 | Server-side WhatsApp bulletin text. (Current: formatted directly in React client). |
| `/v1/tts/synthesize` | `GET` | Phase 4 | Spoken audio stream. (Current: synthesized in browser via Web Speech API). |
| `/v1/bulletin/pdf` | `GET` | Phase 4 | Printable A4 Krishi Bulletin PDF generator for CSC notice boards. |
| `/v1/disaster/flood-risk`| `GET` | Phase 5 | Hydrological surface ponding & flood risk index. |
| `/v1/admin/forecast/refresh`| `POST` | Phase 1 | Administrative cache purge. (Current: automatic 15-min TTL invalidation). |
| `/v1/rules` | `GET` | Phase 3 | Read-only inspection endpoint for active agricultural rules. |
| `/v1/rules/review` | `POST` | Phase 3 | KVK scientist review and feedback submission portal. |

---

## 4. Agricultural Advisory Rule Engine (`rules/rules.yaml`)

The advisory engine evaluates context against 10 declarative rules ranking priority (`high` > `medium` > `low` > `info`):

1. **`no_spray_rain` (Priority: High, Warning):** `rain_mm > 20`. Alerts against chemical spraying and top-dressing urea; advises opening field drainage.
2. **`heat_stress` (Priority: High, Warning):** `tmax_c > 38` during flowering stage. Advises dawn irrigation to prevent floret sterility.
3. **`blast_disease_risk` (Priority: High, Warning):** `humidity > 85 and humidity_days >= 3` on paddy. Warns of fungal blast risk; advises leaf inspection.
4. **`sandy_soil_dry_spell` (Priority: Medium, Warning):** `dry_days >= 7` on sandy soil. Warns of moisture stress; recommends irrigation within 48 hours.
5. **`harvest_rain` (Priority: High, Warning):** `rain_mm > 0` during harvest window. Advises early harvesting and covered grain storage.
6. **`moderate_rain` (Priority: Medium, Warning):** `rain_mm > 5 and rain_mm <= 20`. Advises monitoring field drainage.
7. **`light_rain` (Priority: Low, Success):** `rain_mm > 0 and rain_mm <= 5`. Safe window for light fertilizer application.
8. **`dry_day` (Priority: Low, Info):** `rain_mm == 0`. Advises maintaining normal irrigation schedule.
9. **`chemical_spray_safe_window` (Priority: Low, Advisory):** `rain_mm == 0 and 20 <= tmax_c <= 34`. Identifies optimal morning spray window (07:00–10:30 AM).
10. **`sheath_blight_risk` (Priority: Medium, Warning):** `humidity > 80 and humidity_days >= 2 and tmax_c >= 28` on paddy. Advises lower sheath inspection and avoiding excess nitrogen.

---

## 5. Developer Workflow & Commands

### Running Backend Locally
```bash
# Activate virtual environment
source .venv/bin/activate

# Start server using the backend module path:
uvicorn backend.api:app --reload --port 8000

# Or via the root compatibility shim:
uvicorn api:app --reload --port 8000
```
Interactive Swagger documentation: **http://127.0.0.1:8000/docs**

### Running Test Suite
Execute the authoritative test suite (157 unit tests across backend, pipeline, features, and registry):
```bash
.venv/bin/python -m unittest discover -s tests
```

### Direct Backend Engine Verification
```bash
# Test forecast engine directly
.venv/bin/python backend/forecast_engine_v2.py

# Test advisory engine directly
.venv/bin/python backend/advisory_engine.py

# Test advisory context mapping
.venv/bin/python tests/test_advisory_context.py
```
