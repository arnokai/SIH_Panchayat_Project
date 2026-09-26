"""
Unit and integration tests for world-class weather platform features in TerraMind.
Tests:
1. Accurate Dew Point calculation (Magnus-Tetens)
2. RealFeel® Heat Index & Wind Chill (NOAA Steadman / Rothfusz)
3. Astronomy Ephemeris (Sunrise, Sunset, Solar Noon, Lunar Phase & Illumination %)
4. Air Quality Index (AQI, PM2.5, PM10, Rain Scavenging & Agricultural Health Advice)
5. Solar UV Index with cloud attenuation and safety guidelines
6. Multi-Model Weather Ensemble Consensus (TerraMind 30m, ECMWF, GFS, ICON)
7. Full API payload verification via FastAPI TestClient
"""

import pytest
from datetime import date
from backend.api import get_forecast
from backend.api import app
from backend.weather_metrics_engine import (
    compute_dew_point,
    compute_heat_index,
    compute_astronomy_data,
    compute_air_quality,
    compute_uv_index,
    compute_multi_model_ensemble,
)
from backend.cyclone_engine import fetch_live_radar_timestamps


def test_dew_point_calculation():
    """Verify Magnus-Tetens dew point calculation under various conditions."""
    # When relative humidity is 100%, dew point equals ambient temperature
    dp_100 = compute_dew_point(30.0, 100.0)
    assert abs(dp_100 - 30.0) < 0.2

    # Typical hot & humid Bengal summer condition (34°C, 75% RH)
    dp_humid = compute_dew_point(34.0, 75.0)
    assert 28.0 <= dp_humid <= 30.0

    # Dry condition
    dp_dry = compute_dew_point(25.0, 30.0)
    assert dp_dry < 10.0


def test_heat_index_and_wind_chill():
    """Verify Steadman / Rothfusz RealFeel heat index and wind chill."""
    # Hot & humid: feels much hotter than ambient
    feels_hot = compute_heat_index(35.0, 80.0, wind_kmh=8.0)
    assert feels_hot > 42.0

    # Cold & breezy: wind chill active
    feels_cold = compute_heat_index(10.0, 50.0, wind_kmh=30.0)
    assert feels_cold < 10.0

    # Mild condition
    feels_mild = compute_heat_index(22.0, 50.0, wind_kmh=10.0)
    assert 18.0 <= feels_mild <= 25.0


def test_astronomy_ephemeris():
    """Verify solar and lunar calculations for West Bengal coordinates."""
    # Coordinates for Nadia / Hooghly area (~23.0°N, 88.5°E)
    target_dt = date(2026, 9, 26)
    astro = compute_astronomy_data(23.0, 88.5, target_dt)

    assert "sunrise" in astro
    assert "sunset" in astro
    assert "solar_noon" in astro
    assert "day_length" in astro
    assert "moon_phase" in astro
    assert "moon_icon" in astro
    assert "moon_illumination_pct" in astro
    assert "agricultural_lunar_guidance" in astro

    # Format checks
    assert "AM" in astro["sunrise"]
    assert "PM" in astro["sunset"]
    assert "h " in astro["day_length"] and "m" in astro["day_length"]
    assert 0.0 <= astro["moon_illumination_pct"] <= 100.0
    assert len(astro["agricultural_lunar_guidance"]) > 10


def test_air_quality_and_rain_scavenging():
    """Verify AQI calculation and rain washout scavenging effect."""
    target_dt = date(2026, 9, 26)
    
    # Dry day
    aqi_dry = compute_air_quality(22.5, 88.3, rain_mm=0.0, target_date=target_dt)
    assert "aqi" in aqi_dry
    assert "category" in aqi_dry
    assert aqi_dry["category"] in ["Good", "Satisfactory", "Moderate", "Poor"]
    assert aqi_dry["pm25"] > 0
    assert aqi_dry["pm10"] > aqi_dry["pm25"]
    assert "health_recommendation" in aqi_dry

    # Heavy rain day (should significantly reduce airborne PM via scavenging)
    aqi_rain = compute_air_quality(22.5, 88.3, rain_mm=25.0, target_date=target_dt)
    assert aqi_rain["pm25"] < aqi_dry["pm25"]
    assert aqi_rain["pm10"] < aqi_dry["pm10"]
    assert aqi_rain["aqi"] <= aqi_dry["aqi"]


def test_uv_index_and_cloud_attenuation():
    """Verify UV index calculation and cloud attenuation."""
    target_dt = date(2026, 6, 21) # Summer solstice high sun
    
    # Clear sky
    uv_clear = compute_uv_index(23.0, target_dt, cloud_cover_pct=0.0)
    assert uv_clear["uv_index"] > 8.0
    assert uv_clear["rating"] in ["Very High", "Extreme"]

    # Overcast sky (should attenuate UV)
    uv_overcast = compute_uv_index(23.0, target_dt, cloud_cover_pct=95.0)
    assert uv_overcast["uv_index"] < uv_clear["uv_index"]
    assert "protection_advice" in uv_overcast
    assert "peak_hours" in uv_overcast


def test_multi_model_ensemble():
    """Verify multi-model comparison across 4 world-standard models."""
    ens = compute_multi_model_ensemble(base_rain_p50=18.5, base_tmax=33.0, zone="Delta")
    
    assert "models" in ens
    assert len(ens["models"]) == 4
    
    model_ids = [m["model_id"] for m in ens["models"]]
    assert "terramind_hurdle" in model_ids
    assert "ecmwf_ifs" in model_ids
    assert "gfs_noaa" in model_ids
    assert "icon_dwd" in model_ids

    assert "agreement" in ens
    assert "confidence_pct" in ens
    assert 50 <= ens["confidence_pct"] <= 100
    assert "spread_mm" in ens
    assert ens["spread_mm"] >= 0.0


def test_radar_timestamps_loop():
    """Verify radar animation frames in cyclone_engine."""
    radar = fetch_live_radar_timestamps()
    assert "status" in radar
    assert "host" in radar
    assert "radar_frames" in radar
    assert isinstance(radar["radar_frames"], list)


import json


def test_forecast_api_world_class_metrics():
    """Integration test verifying full forecast API endpoint returns all rich weather metrics."""
    resp = get_forecast(panchayat_id="WB_107778", crop="paddy", days=2, live=False)
    data = json.loads(resp.body.decode("utf-8"))

    # Check live weather current atmospheric metrics
    assert "live_weather" in data
    assert data["live_weather"] is not None
    cw = data["live_weather"]["current"]
    assert "dew_point_c" in cw
    assert "apparent_temperature" in cw
    assert "uv_index" in cw
    assert "uv_rating" in cw
    assert "visibility_km" in cw
    assert "cloud_cover_pct" in cw
    assert "surface_pressure_hpa" in cw
    assert "pressure_tendency" in cw
    assert "wind_compass" in cw

    # Check astronomy block
    assert "astronomy" in data
    astro = data["astronomy"]
    assert "sunrise" in astro
    assert "sunset" in astro
    assert "solar_noon" in astro
    assert "day_length" in astro
    assert "moon_phase" in astro
    assert "moon_icon" in astro
    assert "moon_illumination_pct" in astro

    # Check air quality block
    assert "air_quality" in data
    aqi = data["air_quality"]
    assert "aqi" in aqi
    assert "category" in aqi
    assert "pm25" in aqi
    assert "pm10" in aqi

    # Check multi-model ensemble block
    assert "multi_model_ensemble" in data
    mme = data["multi_model_ensemble"]
    assert len(mme["models"]) == 4
    assert "agreement" in mme
    assert "confidence_pct" in mme
