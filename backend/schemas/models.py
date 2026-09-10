"""
Pydantic v2 Models for TerraMind API
Provides strict typing, request validation, and auto-generated OpenAPI / Swagger documentation.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================
# ROOT & HEALTH SCHEMAS
# ============================================================

class RootResponse(BaseModel):
    name: str = Field(..., description="API Service Name")
    version: str = Field(..., description="API Version")
    status: str = Field(..., description="Service Status")
    docs: str = Field("/docs", description="Swagger Documentation Endpoint")
    health: str = Field("/health", description="Healthcheck Endpoint")
    panchayat_endpoint: str = Field("/v1/panchayats", description="Panchayats Registry Endpoint")
    forecast_endpoint: str = Field("/v1/forecast", description="Forecast Endpoint")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status (ok/error)")
    service: str = Field(..., description="Service Identifier")
    model_version: str = Field(..., description="Active ML Model Identifier")
    rainfall_model: str = Field(..., description="Rainfall Estimation Method")
    statewide_coverage: str = Field(..., description="Geographic scope")
    live_weather_enabled: bool = Field(..., description="Whether live API integration is active")
    degraded: bool = Field(..., description="Whether system is running in degraded fallback mode")
    reason: Optional[str] = Field(None, description="Degradation explanation if degraded is true")


# ============================================================
# PANCHAYAT DISCOVERY & STATEWIDE SCHEMAS
# ============================================================

class PanchayatBrief(BaseModel):
    panchayat_id: str = Field(..., description="Unique Panchayat ID / LGD Code")
    panchayat_name: str = Field(..., description="Official Panchayat Name")


class PanchayatListResponse(BaseModel):
    count: int = Field(..., description="Number of Panchayats listed")
    panchayats: List[PanchayatBrief] = Field(..., description="List of Gram Panchayats")


class DistrictSummary(BaseModel):
    district_name: str = Field(..., description="District Name")
    total_panchayats: int = Field(..., description="Total Gram Panchayats in District")
    total_blocks: int = Field(..., description="Total Community Development Blocks in District")


class StatewideDistrictsResponse(BaseModel):
    state: str = Field("West Bengal", description="State Name")
    district_count: int = Field(..., description="Total rural districts")
    total_panchayats: int = Field(..., description="Total statewide Gram Panchayats")
    districts: List[DistrictSummary] = Field(..., description="District statistics list")


class StatewidePanchayatsResponse(BaseModel):
    state: str = Field("West Bengal", description="State Name")
    total_matched: int = Field(..., description="Total records matching query")
    returned: int = Field(..., description="Number of records returned in page")
    panchayats: List[Dict[str, Any]] = Field(..., description="List of detailed Gram Panchayat records")


class StatewideStatsResponse(BaseModel):
    state: str = Field("West Bengal", description="State Name")
    total_rows: int = Field(..., description="Total historical rows in data lake")
    total_panchayats: int = Field(..., description="Total Gram Panchayats covered")
    total_blocks: int = Field(..., description="Total CD Blocks covered")
    total_districts: int = Field(..., description="Total Districts covered")
    date_range: str = Field(..., description="Historical timeline coverage")
    qa_status: str = Field(..., description="Automated QA status (PASS/PENDING)")
    storage_format: str = Field(..., description="Underlying data format")
    memory_optimization: str = Field(..., description="Performance profile")


class NearestPanchayatResponse(BaseModel):
    status: str = Field("ok", description="Status string")
    nearest_panchayat: Dict[str, Any] = Field(..., description="Closest Gram Panchayat record with distance_km")
    nearby_panchayats: List[Dict[str, Any]] = Field(default_factory=list, description="Top closest Gram Panchayats with distance_km")


# ============================================================
# FORECAST & AGRONOMIC SCHEMAS
# ============================================================

class QuantileRain(BaseModel):
    p10: Optional[float] = Field(None, description="10th percentile rainfall (Minimum dry bound in mm)")
    p50: float = Field(..., description="50th percentile rainfall (Expected median in mm)")
    p90: Optional[float] = Field(None, description="90th percentile rainfall (Worst-case runoff/flood risk in mm)")


class TMaxObj(BaseModel):
    p50: float = Field(..., description="Expected Maximum Temperature in °C")
    p10: Optional[float] = Field(None, description="10th percentile temperature in °C")
    p90: Optional[float] = Field(None, description="90th percentile temperature in °C")


class AdvisoryDetail(BaseModel):
    rule_id: str = Field(..., description="Agricultural Rule Code")
    priority: str = Field(..., description="Priority level (high, medium, low, none)")
    type: str = Field(..., description="Action category (spraying, irrigation, disease, harvest)")
    text: Optional[str] = Field(None, description="Primary advisory text")
    text_en: str = Field(..., description="English agronomic guidance copy")
    text_bn: Optional[str] = Field(None, description="Bengali agronomic translation")


class AdvisorySummaryItem(BaseModel):
    date: str = Field(..., description="ISO Forecast Date (YYYY-MM-DD)")
    rule_id: str = Field(..., description="Triggered Rule ID")
    priority: str = Field(..., description="Priority Level")
    type: str = Field(..., description="Action Category")
    text: Optional[str] = Field(None, description="Primary guidance copy")
    text_en: str = Field(..., description="English Guidance")
    text_bn: Optional[str] = Field(None, description="Bengali Translation")


class DailyForecast(BaseModel):
    date: str = Field(..., description="ISO Forecast Date (YYYY-MM-DD)")
    rain_mm: QuantileRain = Field(..., description="Quantile downscaled rainfall bounds")
    rain_probability: float = Field(..., description="Probability of precipitation (0.0 to 1.0)")
    tmax_c: TMaxObj = Field(..., description="Maximum temperature quantiles")
    tmin_c: float = Field(..., description="Minimum temperature in °C")
    advisory: AdvisoryDetail = Field(..., description="Primary agricultural advisory for the day")


class CurrentWeather(BaseModel):
    time: Optional[str] = Field(None, description="Timestamp of telemetry (ISO format)")
    temperature_2m: float = Field(..., description="2m Air Temperature in °C")
    relative_humidity_2m: Optional[float] = Field(None, description="Relative Humidity percentage")
    wind_speed_10m: Optional[float] = Field(None, description="10m Wind Speed in km/h")
    precipitation: Optional[float] = Field(0.0, description="Precipitation accumulation in mm")
    weather_code: Optional[int] = Field(None, description="WMO Weather Code")
    apparent_temperature: Optional[float] = Field(None, description="Apparent / heat index temperature in °C")
    interval: Optional[int] = Field(None, description="Observation interval seconds")
    raw_temperature_2m: Optional[float] = Field(None, description="Raw unadjusted grid temperature in °C")
    elevation_lapse_c: Optional[float] = Field(None, description="DEM elevation lapse rate adjustment in °C")


class HourlyRecord(BaseModel):
    time: str = Field(..., description="ISO timestamp")
    hour: str = Field(..., description="Hour in 24h format (HH:MM)")
    display_time: str = Field(..., description="User-friendly hour (e.g., 2 PM)")
    temperature_c: float = Field(..., description="Temperature in °C")
    precipitation_probability: float = Field(..., description="Rain chance (0-100%)")
    precipitation_mm: float = Field(..., description="Rain amount in mm")
    wind_speed_kmh: float = Field(..., description="Wind speed in km/h")
    weather_code: int = Field(..., description="WMO weather code")
    spray_safety: str = Field(..., description="Safety status: optimal, caution, unsafe_rain, unsafe_wind")
    spray_safety_label: str = Field(..., description="Human-readable operational spray label")
    is_daylight: bool = Field(..., description="Whether the hour is during sunlight hours")


class HourlyWeather(BaseModel):
    time: Optional[List[str]] = None
    temperature_2m: Optional[List[float]] = None
    relative_humidity_2m: Optional[List[float]] = None
    wind_speed_10m: Optional[List[float]] = None
    precipitation_probability: Optional[List[float]] = None
    precipitation: Optional[List[float]] = None
    weather_code: Optional[List[int]] = None
    records: Optional[List[HourlyRecord]] = None
    all_records: Optional[List[HourlyRecord]] = None


class OperationalRefinement(BaseModel):
    status: Optional[str] = None
    elevation_m: Optional[float] = None
    base_elevation_m: Optional[float] = None
    relative_elevation_m: Optional[float] = None
    lapse_rate_c: Optional[float] = None
    apparent_temp_c: Optional[float] = None
    canopy_humidity_pct: Optional[float] = None
    spray_drift_risk: Optional[str] = None


class LiveWeatherPayload(BaseModel):
    current: Optional[CurrentWeather] = None
    hourly: Optional[HourlyWeather] = None
    operational_insight: Optional[str] = None
    operational_refinement: Optional[OperationalRefinement] = None


class CoarseCoordinate(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")


class ForecastResponse(BaseModel):
    panchayat_id: str = Field(..., description="Target Panchayat Identifier")
    panchayat_name: str = Field(..., description="Official Gram Panchayat Name")
    block_name: Optional[str] = Field(None, description="CD Block Name")
    district_name: Optional[str] = Field(None, description="District Name")
    crop: str = Field(..., description="Active crop context")
    issued_at: Optional[str] = Field(None, description="ISO timestamp of forecast generation")
    model_version: str = Field(..., description="Downscaling ML model release")
    rainfall_model: str = Field(..., description="Rainfall methodology")
    is_live_dynamic: bool = Field(..., description="True if using live ECMWF/GFS stream")
    source: str = Field(..., description="Data lineage and provider")
    coarse_coordinate: CoarseCoordinate = Field(..., description="Grid centroid coordinate")
    forecast: List[DailyForecast] = Field(..., description="5-day downscaled forecast horizon")
    advisories: List[AdvisorySummaryItem] = Field(..., description="Active agricultural advisories")
    live_weather: Optional[LiveWeatherPayload] = Field(None, description="24-hour hourly weather and operational spraying telemetry")
    degraded: bool = Field(False, description="Degraded mode indicator")
    degraded_reason: Optional[str] = Field(None, description="Explanation when running in degraded fallback mode")
