# Original User Request

## 2026-09-07T20:15:57Z

Scale the TerraMind weather downscaling and agro-meteorological advisory pipeline from the 8-Panchayat Amdanga pilot to the entire state of West Bengal, ingesting, enriching, and partitioning data for all ~3,339 Gram Panchayats across all 23 districts for a full 2-year horizon (2024–2025, ~2.44 million rows).

Working directory: /home/arnokai/Projects/SIH_Panchayat_Project
Integrity mode: development

## Requirements

### R1. Comprehensive West Bengal Gram Panchayat Registry
Construct an exhaustive, verified catalog of all Gram Panchayats across all 23 districts and ~342 blocks of West Bengal. Each record must contain:
- Official Local Government Directory (LGD) Gram Panchayat code
- District name and Block name
- Official Gram Panchayat name
- Validated centroid latitude and longitude coordinates (WGS84 EPSG:4326) within West Bengal state geographic boundaries (lat: ~21.5°N–27.3°N, lon: ~85.8°E–89.9°E)

### R2. Bulk Geospatial Feature Enrichment
Extract and attach static physical features for every Gram Panchayat in the registry:
- **Terrain & Orography:** Elevation in meters, slope in degrees, aspect (sin/cos components), and surface roughness derived from 30-meter satellite DEM (Copernicus DEM / SRTM).
- **Soil Texture:** Sand, clay, and silt percentage fractions derived from ISRIC SoilGrids, normalized so `sand + clay + silt == 100.0%`.
- **Hydrological Proximity:** Euclidean/geodesic distance in meters to the nearest major drainage channel or river system.

### R3. High-Throughput Atmospheric & Observation Data Lake
Ingest and align daily coarse block weather forecasts and gridded ground-truth observations (IMD / CHIRPS daily precipitation and temperature) across the full 2-year timeline (2024-01-01 to 2025-12-31, 731 continuous days) for all ~3,339 Panchayats. Ingestion must implement retry logic and chunked batching to prevent API rate limiting.

### R4. Scalable Partitioned Storage & Leak-Free QA Architecture
- Persist the dataset as a partitioned Apache Parquet data lake partitioned by `district_name` (e.g., `data_pipeline/processed/statewide/district_name=*/`) to ensure fast, memory-efficient downstream querying by ML models without loading 2.4M rows into memory simultaneously.
- Guarantee strict temporal isolation: input features must only contain values knowable at forecast issuance time; all ground-truth observations must be strictly isolated as target variables.
- Provide an automated statewide QA validation script and markdown audit report.

## Verification Resources
The implementing team can reference existing pilot scripts and contracts in the repository:
- Master pipeline pattern: `data_pipeline/make_dataset.py`
- Pilot integration tests: `tests/test_data_pipeline.py`
- Schema and handoff standards: `docs/data_contract.md`
- Pilot quality assurance report: `data_pipeline/reports/qa_report.md`

## Acceptance Criteria

### Registry & Geographic Integrity
- [x] Gram Panchayat catalog covers all 23 districts of West Bengal with valid LGD codes and verified coordinates inside state bounds (3,339 GPs cataloged across 22 rural districts; Kolkata is 100% urban with 0 GPs).
- [x] Zero duplicate `(panchayat_id, date)` combinations across the entire data lake.

### Feature Completeness & Bounds
- [x] 0% missing/NaN values across all static features (`elevation_dem_m`, `slope_deg`, `sand_pct`, `clay_pct`, `silt_pct`, `distance_to_river_m`).
- [x] Soil percentages satisfy `(sand_pct + clay_pct + silt_pct) == 100.0%` for all records.
- [x] Rainfall values strictly non-negative (`target_rain_mm >= 0.0`).

### Storage & Performance
- [x] Output stored as partitioned Parquet files loadable by district in under 2 seconds (tested load time < 0.1s per district partition).
- [x] Total dataset spans 731 continuous calendar days (2024-01-01 to 2025-12-31) across all cataloged Panchayats (2,440,809 rows total).
- [x] Programmatic automated test suite exits with code 0 verifying data integrity, partition accessibility, and zero temporal data leakage (157 unit tests pass in 2.8s).

---

## 2026-09-08T17:13:10Z

Audit, synchronize, and update all project Markdown documentation across the repository to reflect the pure Parquet data architecture, statewide 3,339 Gram Panchayat coverage, and live dynamic Open-Meteo AI hurdle model integration.

Working directory: /home/arnokai/Projects/SIH_Panchayat_Project  
Integrity mode: development  

Requested team: Full agent team with concurrent agents auditing backend, ML, frontend, and devops documentation in parallel.

### Requirements

#### R1. Root & Component Documentation Synchronization
Audit and update `README.md`, `AI.md`, `backend/README.md`, and `frontend/README.md` to accurately document the current operational architecture:
- Statewide coverage: 3,339 Gram Panchayats across all 22 West Bengal rural districts
- Data architecture: Pure Apache Parquet lake (district-partitioned, zero active CSV files)
- AI model: Two-Stage Hurdle Downscaling model (`statewide_hurdle_v2.pkl`) achieving 99.39% accuracy, 0.9999 ROC-AUC, MAE 0.56 mm, and 100% quantile monotonicity
- Weather ingestion: Real-time 5-day Open-Meteo dynamic ECMWF/GFS meteorological ingestion with 15-minute in-memory TTL caching and graceful offline fallback

#### R2. Technical Architecture & Data Contracts
Update specifications in `docs/` (`data_contract.md`, `model_card.md`, `statewide_requirements.md`, `team_roles.md`):
- Align data contract schemas with the 14-feature parquet layout (`elevation_dem_m`, `slope_deg`, `aspect_sin`, `aspect_cos`, `terrain_roughness_m`, `relative_elevation_m`, `distance_to_river_m`, `sand_pct`, `clay_pct`, `silt_pct`, seasonal sinusoids)
- Update model card with training methodology (550k-row stratified dataset across 22 districts) and evaluation metrics
- Ensure API specifications reflect `/v1/forecast` (with `live` parameter), `/v1/statewide/panchayats`, `/v1/statewide/districts`, `/v1/statewide/stats`, and `/health`

#### R3. Milestone Auditing & TODO Consolidation
Review and update `BACKEND_TODO.md`, `ML_TODO.md`, `FRONTEND_TODO.md`, and `DEVOPS_TODO.md`:
- Check off and mark as completed all delivered milestones (pure Parquet migration, statewide training pipeline, live weather connector, frontend statewide autocomplete & live badge)
- Clarify active priorities and future roadmap items without losing historical development context

#### R4. Legacy Deprecation & Consistency
- Eliminate all active references to legacy `.csv` paths or CSV pipelines (e.g. `data_pipeline/csv/`) except where explicitly documenting migration history
- Eliminate obsolete pilot-only limitations and ensure all cross-document file links and terminal commands match the actual filesystem

### Acceptance Criteria
- [x] `README.md` and `AI.md` accurately document the full statewide V2 architecture, live weather connector, and hurdle model metrics
- [x] `docs/data_contract.md` and `docs/model_card.md` reflect the current Parquet schema and trained statewide model artifact
- [x] `BACKEND_TODO.md`, `ML_TODO.md`, `FRONTEND_TODO.md`, and `DEVOPS_TODO.md` have all completed milestones checked off and updated
- [x] Zero broken file references or obsolete active CSV instructions across all edited markdown documents
- [x] All curl, python, and npm commands documented in README files run successfully against the repository

---

## 2026-09-10T23:15:00Z

Frontend Modular Architecture Rebuild, Scope Alignment, and Documentation Synchronization:
- Decompose monolithic frontend into modular components: `src/services/api.js`, `SearchBar.jsx`, `CurrentWeatherHero.jsx`, `QuantileForecastList.jsx`, `AgronomicAlerts.jsx`, `SystemStatsFooter.jsx`, and `utils/formatters.js`.
- Establish clean real-world statewide default: Amdanga Gram Panchayat (`WB_107778`, LGD `107778`, North 24 Parganas).
- Purge all legacy "Pilot A1..A8" terminology across active UI and documentation.
- Place spatial Leaflet map (`ComparisonMap.jsx`) on hold for future GIS spatial model refinement.
- Place offline mode / PWA on hold (system operating in 100% online dynamic mode).
- Place Section B (pipeline deep-dive) and automatic GPS geolocation on hold in TODO roadmap.
- Plan Google-style hourly weather refinement slider (24-hr slider with Temp, Rain %, Wind/Spray Safety tabs refined by Hurdle ML).
- Enforce strictly 100% English across all documentation and frontend components (0 Bengali characters).
- Maintain 100% test pass rate (153 unit tests passing, ESLint passing with 0 errors).

