# Model Card — TerraMind V2 Weather Downscaler

## Model Details
* **Developed by:** TerraMind SIH Team (Problem Statement SIH26074)
* **Model Type:** Gradient-Boosted Trees (XGBoost Regressor / Classifier) & Hurdle Architecture
* **Target Region:** Amdanga Block, North 24 Parganas, West Bengal, India
* **Primary Target Unit:** 8 Gram Panchayats (Adhata, Amdanga, Beraberia, Bodai, Chandigarh, Maricha, Sadhanpur, Taraberia)

## Intended Use
* **Primary Use:** Providing localized agro-meteorological advisories and downscaled weather context for smallholder farmers and KVK scientists.
* **Out-of-Scope:** Aviation, dam emergency discharge operations, crop insurance dispute adjudication without ground validation.

## Factors & Feature Mechanisms
* **Elevation & Topography:** SRTM 30m Digital Elevation Model (`elevation_dem_m`, `slope_deg`, `aspect_sin`, `aspect_cos`, `terrain_roughness_m`)
* **Hydrology:** Distance to major rivers (`distance_to_river_m`)
* **Gridded Inputs:** IMERG and IMD gridded precipitation (`imerg_rain_mm`, `imd_rain_mm`)
* **Temporal & Seasonal:** Lagged precipitation (`rain_lag_1` to `7`) and trigonometric day-of-year cyclics (`day_of_year_sin`, `day_of_year_cos`)

## Performance & Ethical Safeguards
* **Rain Event Detection:** POD = 0.91 (detects 91% of rainy events)
* **Operational Fallback:** When multi-day spatial downscaling cannot reliably beat coarse baselines across flat terrain, the system automatically falls back to official block forecasts with `"degraded": true` rather than presenting unvalidated micro-forecasts.
