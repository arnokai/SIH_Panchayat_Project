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
- [ ] Gram Panchayat catalog covers all 23 districts of West Bengal with valid LGD codes and verified coordinates inside state bounds.
- [ ] Zero duplicate `(panchayat_id, date)` combinations across the entire data lake.

### Feature Completeness & Bounds
- [ ] 0% missing/NaN values across all static features (`elevation_dem_m`, `slope_deg`, `sand_pct`, `clay_pct`, `silt_pct`, `distance_to_river_m`).
- [ ] Soil percentages satisfy `(sand_pct + clay_pct + silt_pct) == 100.0%` for all records.
- [ ] Rainfall values strictly non-negative (`target_rain_mm >= 0.0`).

### Storage & Performance
- [ ] Output stored as partitioned Parquet files loadable by district in under 2 seconds.
- [ ] Total dataset spans 731 continuous calendar days (2024-01-01 to 2025-12-31) across all cataloged Panchayats (~2.44M rows total).
- [ ] Programmatic automated test suite exits with code 0 verifying data integrity, partition accessibility, and zero temporal data leakage.
