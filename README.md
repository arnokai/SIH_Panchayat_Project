# TerraMind V2 — Panchayat-Level Weather Intelligence & Agricultural Advisory

> **V2 development branch:** `v2-development`
> **Repository:** `https://github.com/arnokai/SIH_Panchayat_Project`
> **Current role:** Research/prototype decision-support system for the Amdanga study area, North 24 Parganas.

TerraMind V2 extends the earlier V0/V1/V1.3 work into a more complete **forecast + agricultural-advisory application**.

---

## 🚀 Quick Start

### Requirements
- Python 3.9+ (tested on Python 3.14)
- Node.js + npm
- Git

### Step 1 — Clone the repo

```bash
git clone -b v2-development https://github.com/arnokai/SIH_Panchayat_Project.git
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
# With venv activated:
uvicorn api:app --reload

# Or directly without activating (works in any shell):
.venv/bin/uvicorn api:app --reload
```

Backend runs at: **http://127.0.0.1:8000**
API docs at: **http://127.0.0.1:8000/docs**

### Step 4 — Start the frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Dashboard runs at: **http://localhost:5173**

---

## 1. What Changed in V2?

The main V2 change is a move from a primarily model-centric prototype toward a **decision-support pipeline**:

```text
Panchayat
   ↓
Forecast input
   ↓
5-day forecast delivery
   ↓
Forecast context builder
   ↓
Crop calendar + soil context
   ↓
Rule engine
   ↓
English + Bengali advisory
   ↓
FastAPI
   ↓
React dashboard + Panchayat comparison map
```

### V2 adds

| Area | V1 / V1.3 | V2 |
|---|---|---|
| Forecast delivery | Earlier model experiments | 5-day forecast API |
| Panchayat selection | Basic | Panchayat-specific V2 API + dashboard |
| Agricultural logic | Basic rules | Context-aware advisory engine |
| Crop context | Limited | Crop + crop-stage lookup |
| Soil context | Earlier feature experiments | SoilGrids-derived soil classification |
| Dry spell logic | Not operationalized | Forecast-aware dry-day context |
| Humidity context | Earlier weather data | Consecutive high-humidity context available for advisory rules |
| Advisory language | English/Bengali | English + Bengali API output |
| Crop selection | Limited | `paddy` / `vegetables` in dashboard |
| Map | Earlier dashboard concept | Panchayat comparison map |
| API status | Prototype API | V2 `/v1/...` endpoints |
| Model safety | Multiple experimental models | Conservative fallback for operational delivery |

---

# 2. Important V2 Forecasting Decision

V2 contains downscaling experiments, but the experimental Panchayat ML downscaling model is **not promoted to the operational five-day forecast**.

The V2 delivery layer therefore uses a **coarse block forecast fallback** rather than presenting an insufficiently validated Panchayat ML forecast as if it were reliable.

The API explicitly reports this state:

```json
{
  "degraded": true,
  "degraded_reason": "Operational five-day Panchayat ML downscaling is not yet validated."
}
```

This is intentional.

### Why?

The M3 downscaling experiments showed useful overall error reduction on a clean test split, but spatial verification showed that the model did not reproduce the observed Panchayat-to-Panchayat rainfall variability strongly enough for operational multi-day use.

Therefore:

> **V2 prioritizes honest forecast delivery over claiming unsupported Panchayat-level ML accuracy.**

The experimental model artifacts are retained for research and future improvement.

---

# 3. V2 Forecast Delivery

The V2 forecast engine is:

```text
forecast_engine_v2.py
        ↓
coarse block forecast
        ↓
Panchayat-specific context
        ↓
advisory engine
        ↓
API response
```

The forecast currently supports:

- Panchayat ID
- 1–5 forecast days
- Crop selection
- Rainfall amount
- Rain probability
- Maximum temperature
- Minimum temperature
- Advisory information
- Degraded/fallback status
- Source information
- Issue time in IST

Example Panchayat IDs:

```text
A1 → ADHATA
A2 → AMDANGA
A3 → BERABERIA
A4 → BODAI
A5 → CHANDIGARH
A6 → MARICHA
A7 → SADHANPUR
A8 → TARABERIA
```

---

# 4. V2 Agricultural Advisory Engine

V2 separates advisory logic from the forecast engine.

Main files:

```text
advisory_context.py
advisory_engine.py
forecast_advisory_context.py
rules.yaml
data/crop_calendar.py
data/crop_calendar.yaml
```

### Advisory flow

```text
Forecast
   +
Panchayat context
   +
Crop
   +
Crop stage
   +
Soil type
   +
Dry/humidity context
        ↓
   Rule evaluation
        ↓
   Highest-priority matching rule
        ↓
English + Bengali advisory
```

This makes the advisory system easier to modify than hard-coding every recommendation inside the API.

---

# 5. V2 Rule Categories

The current `rules.yaml` contains the following prototype rules.

### Rainfall

```text
rain_mm > 20
→ Do not spray, do not apply urea, open field drains.
```

```text
rain_mm > 5 and rain_mm <= 20
→ Moderate-rain advisory.
```

```text
rain_mm > 0 and rain_mm <= 5
→ Light-rain advisory.
```

```text
rain_mm == 0
→ Dry-day information.
```

### Heat stress

```text
crop = paddy
stage = flowering
tmax_c > 38
→ Paddy heat-stress advisory.
```

### High humidity / disease risk

```text
humidity > 85
and humidity_days >= 3
→ Paddy blast-disease risk advisory.
```

### Dry spell

```text
soil = sandy
and dry_days >= 7
→ Irrigation advisory.
```

### Harvest rain

```text
stage = harvest
and rain_mm > 0
→ Advance harvest / covered-storage advisory.
```

> These are **prototype rules**. Thresholds and agricultural actions should be reviewed with an agriculture faculty member / KVK scientist before being described as validated recommendations.

---

# 6. Crop Calendar

V2 introduces a small crop-calendar layer:

```text
data/crop_calendar.yaml
data/crop_calendar.py
```

Current prototype calendar:

```text
Crop: paddy
Variety group: aman
Region: Amdanga block

Flowering:
approximately 15 Sep → 05 Oct

Harvest:
approximately 01 Nov → 15 Dec
```

The flowering window reflects the representative late-September Aman scenario used in the project design.

The calendar is a **prototype context layer**, not a fully validated local crop calendar for every Panchayat.

---

# 7. Soil Context

V2 adds soil context using SoilGrids-derived surface soil properties.

Main files:

```text
data/download_soil_context.py
data/classify_soil_context.py
data/raw/panchayat_soil_features.csv
data/raw/panchayat_soil_context.csv
```

The prototype currently classifies the eight study Panchayats conservatively.

Current result:

```text
A1 → non_sandy
A2 → non_sandy
A3 → non_sandy
A4 → non_sandy
A5 → non_sandy
A6 → non_sandy
A7 → non_sandy
A8 → non_sandy
```

Therefore the sandy-soil dry-spell rule currently does not trigger for these Panchayats.

---

# 8. Historical Advisory Context

V2 also builds historical context used by the advisory layer.

### High-humidity streaks

```text
data/build_humidity_context.py
data/raw/advisory_weather_history.csv
```

Tracks consecutive days where:

```text
humidity_pct > 85%
```

### Dry spells

```text
data/build_dry_spell_context.py
data/raw/advisory_context_history.csv
```

Tracks consecutive days with:

```text
rain_mm == 0
```

The forecast-aware context builder then combines the latest observed streak with future forecast rainfall instead of blindly copying the historical streak into every forecast day.

---

# 9. V2 API

Main backend:

```text
api.py
```

Main forecast engine:

```text
forecast_engine_v2.py
```

## Endpoints

### Health

```text
GET /health
```

Browser:

```text
http://127.0.0.1:8000/health
```

### List Panchayats

```text
GET /v1/panchayats
```

Browser:

```text
http://127.0.0.1:8000/v1/panchayats
```

### Forecast

```text
GET /v1/forecast?panchayat_id=A2&days=5&lang=bn&crop=paddy
```

Example:

```text
http://127.0.0.1:8000/v1/forecast?panchayat_id=A2&days=5&lang=bn&crop=paddy
```

### FastAPI documentation

```text
http://127.0.0.1:8000/docs
```

---

# 10. Example V2 Forecast Response

A simplified response looks like:

```json
{
  "panchayat_id": "A2",
  "panchayat_name": "AMDANGA",
  "crop": "paddy",
  "model_version": "V2",
  "rainfall_model": "Coarse forecast fallback",
  "degraded": true,
  "forecast": [
    {
      "date": "2026-09-01",
      "rain_mm": 8.7,
      "tmax_c": 29.1,
      "rain_probability": 1.0,
      "advisory": {
        "rule_id": "moderate_rain"
      }
    }
  ]
}
```

The exact response structure may evolve during V2 development.

---

# 11. V2 Frontend

The frontend is built with:

```text
React
Vite
React Leaflet
Leaflet
```

Main files:

```text
frontend/src/App.jsx
frontend/src/App.css
frontend/src/ComparisonMap.jsx
```

### Current dashboard capabilities

- Panchayat selector
- Crop selector
- Five-day forecast cards
- Rainfall information
- Temperature information
- Bengali advisory
- Advisory priority/type
- Panchayat comparison map
- System/degraded status
- API-driven forecast data

The comparison map is an important V2 feature because the project is intended to work at **Panchayat level rather than only block level**.

---

# 12. Running V2 Locally

## Backend terminal

From the repository root:

```bash
# Linux / macOS (Bash / Zsh)
source .venv/bin/activate
uvicorn api:app --reload
```

```fish
# Linux / macOS (Fish shell)
source .venv/bin/activate.fish
uvicorn api:app --reload
```

```bash
# Direct execution (Works in any shell without activating):
.venv/bin/uvicorn api:app --reload
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
uvicorn api:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Docs:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend terminal

Open a second terminal window:

```bash
cd frontend
npm install
npm run dev
```

Vite normally prints the local dashboard URL.

Typical address:

```text
http://localhost:5173
```

---

# 13. Fresh Laptop Setup

### Linux / macOS (Bash / Zsh)

```bash
git clone -b v2-development https://github.com/arnokai/SIH_Panchayat_Project.git
cd SIH_Panchayat_Project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --reload
```

### Linux / macOS (Fish shell)

```fish
git clone -b v2-development https://github.com/arnokai/SIH_Panchayat_Project.git
cd SIH_Panchayat_Project
python3 -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements.txt
uvicorn api:app --reload
```

### Windows PowerShell

```powershell
git clone -b v2-development https://github.com/arnokai/SIH_Panchayat_Project.git
cd SIH_Panchayat_Project
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn api:app --reload
```

Then in a second terminal (any OS):

```bash
cd SIH_Panchayat_Project/frontend
npm install
npm run dev
```

> **Important:** clone `v2-development`, not `main`, when you want the current V2 system.

---

# 14. V2 Files Added

The main V2 additions are:

```text
advisory_context.py
advisory_engine.py
forecast_advisory_context.py
forecast_engine_v2.py

data/__init__.py
data/crop_calendar.py
data/crop_calendar.yaml
data/build_dry_spell_context.py
data/build_humidity_context.py
data/download_soil_context.py
data/classify_soil_context.py
data/download_coarse_forecast.py
data/download_coarse_history.py

frontend/src/ComparisonMap.jsx

tests/test_advisory_context.py
tests/test_advisory_rules.py
tests/test_forecast_advisories.py
```

V2 also includes new forecasting/downscaling experiment and training scripts under `data/` and the project root.

---

# 15. V2 Model Artifacts

Research/downscaling artifacts are kept separately from the operational delivery decision.

Current V2 model files:

```text
models/v2_downscaling_metadata.pkl        (excluded from git — research only)
models/v2_downscaling_rain_classifier.pkl (excluded from git — research only)
models/v2_downscaling_rain_regressor.pkl  (excluded from git — research only)
```

> These model artifacts are intentionally excluded from the repository. Regenerate by running `train_pipeline_v2_downscaling.py`.

These are retained for development/research.

The current five-day delivery layer does **not** present the experimental ML downscaler as a validated operational Panchayat forecast.

---

# 16. V2 Data Sources / Context

The V2 pipeline uses or prepares context from:

```text
Historical weather
Open-Meteo forecast
Panchayat coordinates
SoilGrids soil properties
Crop calendar
Humidity history
Dry-spell history
Earlier rainfall/model experiments
```

The project continues to keep large external source/raster datasets outside Git where appropriate.

---

# 17. Testing

V2 includes focused advisory and context integration tests in the `tests/` directory:

```bash
# Run all tests
python tests/test_advisory_context.py
python tests/test_advisory_rules.py
python tests/test_forecast_advisories.py

# Or with pytest
pytest tests/
```

The intended checks include:

```text
Panchayat → soil context
Panchayat + date → crop stage
Forecast → advisory context
Rule threshold → correct advisory
Bengali advisory → valid API output
```

The handbook also emphasizes API tests, data validation, model tests, and end-to-end integration tests as the project matures.

---

# 18. Current V2 Limitations

V2 is still a **research/prototype system**.

Important limitations:

- The operational five-day Panchayat ML downscaling model is not yet validated.
- The current delivery layer therefore uses a coarse forecast fallback.
- Rainfall references are gridded products rather than direct Panchayat rain-gauge observations.
- The study area currently contains eight Panchayats.
- Crop-calendar timings are prototype context and need local validation.
- Advisory thresholds/actions need agriculture-domain review before real deployment.
- The system should not replace official weather or agricultural advisories.

---

# 19. V1.3 → V2 in One View

```text
V1
│
├── Basic ML rainfall / rain probability / Tmax
│
↓
V1.1
│
├── Terrain features
│
↓
V1.2
│
├── IMD + IMERG + CHIRPS experiments
├── CHIRPS T+1 rainfall target
│
↓
V1.3
│
├── Multi-source rainfall calibration
├── Residual correction
│
↓
V2
│
├── 5-day forecast delivery
├── Conservative forecast fallback
├── Forecast-aware context
├── Crop calendar
├── Soil context
├── Humidity / dry-spell context
├── Rule-based advisory engine
├── English + Bengali advisory API
├── Crop selector
├── Panchayat comparison map
├── Improved FastAPI layer
└── Focused advisory tests
```

---

# 20. Development Philosophy

V2 follows one important principle:

> **Do not claim more forecast accuracy than the validation evidence supports.**

The system should provide useful localized decision support while making the current limitations visible.

Future V2.x work can focus on:

```text
better spatial downscaling
independent station/AWS validation
stronger heavy-rainfall handling
forecast uncertainty
better local crop calendars
agriculture-domain validation
```

---

## TerraMind

**TerraMind — Understand Earth. Empower Futures.**

Panchayat-level environmental intelligence for agricultural decision support.
