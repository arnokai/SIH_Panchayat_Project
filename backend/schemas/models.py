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
    crop: Optional[str] = Field(None, description="Target crop for this advisory")
    crop_stage: Optional[str] = Field(None, description="Phenological growth stage")
    source: Optional[str] = Field(None, description="Authoritative agricultural institution source")
    action_items: Optional[List[str]] = Field(default_factory=list, description="Structured checklist of actionable field steps")
    text: Optional[str] = Field(None, description="Primary advisory text")
    text_en: str = Field(..., description="English agronomic guidance copy")
    text_bn: Optional[str] = Field(None, description="Bengali agronomic translation")


class AdvisorySummaryItem(BaseModel):
    date: str = Field(..., description="ISO Forecast Date (YYYY-MM-DD)")
    rule_id: str = Field(..., description="Triggered Rule ID")
    priority: str = Field(..., description="Priority Level")
    type: str = Field(..., description="Action Category")
    crop: Optional[str] = Field(None, description="Target crop for this advisory")
    crop_stage: Optional[str] = Field(None, description="Phenological growth stage")
    source: Optional[str] = Field(None, description="Authoritative agricultural institution source")
    required_source: Optional[str] = Field(None, description="Mandatory national/state research institute for this crop")
    bulletin_ref: Optional[str] = Field(None, description="Official IMD AAS bulletin reference number")
    action_items: Optional[List[str]] = Field(default_factory=list, description="Structured checklist of actionable field steps")
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
    dew_point_c: Optional[float] = Field(None, description="Dew point condensation temperature in °C")
    uv_index: Optional[float] = Field(None, description="Ultraviolet index (0-11+)")
    uv_rating: Optional[str] = Field(None, description="UV danger level (Low/Moderate/High/Extreme)")
    visibility_km: Optional[float] = Field(None, description="Atmospheric visibility in km")
    cloud_cover_pct: Optional[float] = Field(None, description="Cloud cover percentage")
    surface_pressure_hpa: Optional[float] = Field(None, description="Barometric surface pressure in hPa")
    pressure_tendency: Optional[str] = Field(None, description="Pressure trend: Rising / Steady / Falling")
    wind_direction_deg: Optional[float] = Field(None, description="Wind heading in degrees")
    wind_compass: Optional[str] = Field(None, description="Wind cardinal direction (e.g. SSW)")
    spray_suitability: Optional[Dict[str, Any]] = Field(None, description="Agrochemical spray window safety analysis")
    water_balance: Optional[Dict[str, Any]] = Field(None, description="FAO-56 crop water requirement and irrigation balance")


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
    astronomy: Optional[Dict[str, Any]] = None
    air_quality: Optional[Dict[str, Any]] = None
    multi_model_ensemble: Optional[Dict[str, Any]] = None


# ============================================================
# LIVE AGROMET BULLETIN SCHEMAS
# ============================================================

class AgrometBulletinCropAdvisory(BaseModel):
    crop: str = Field(..., description="Crop identifier")
    advisory_summary: str = Field(..., description="Brief headline summary")
    agronomic_guidance: str = Field(..., description="Detailed technical guidance")
    action_checklist: List[str] = Field(default_factory=list, description="Operational field tasks")
    required_source: str = Field(..., description="Citing authority")
    amfu_center: str = Field(..., description="Issuing Agromet Field Unit")


class AgrometBulletinResponse(BaseModel):
    status: str = Field("success", description="Status string")
    verification_status: str = Field("OFFICIAL_IMD_GKMS_VERIFIED", description="Official authenticity verification")
    bulletin_number: str = Field(..., description="Official IMD AAS bulletin reference code")
    issue_date: str = Field(..., description="Bi-weekly bulletin release date")
    valid_until: str = Field(..., description="Advisory validity window end date")
    district: str = Field(..., description="Target district")
    block: Optional[str] = Field(None, description="Target CD block")
    state: str = Field("West Bengal", description="State name")
    amfu_center: str = Field(..., description="Designated Agromet Field Unit")
    university: str = Field(..., description="Nodal Agricultural University")
    lead_scientist: str = Field(..., description="Principal Agrometeorologist")
    amfu_code: str = Field(..., description="Official AMFU code")
    selected_crop: str = Field(..., description="Target crop")
    crop_name: str = Field(..., description="Crop display name")
    required_source: str = Field(..., description="Mandatory ICAR institute source")
    required_source_short: str = Field(..., description="Short institute acronym")
    required_mandate: str = Field(..., description="Institutional mandate")
    required_source_url: str = Field(..., description="Official institute portal URL")
    official_portal_url: str = Field(..., description="Official IMD Agromet portal URL")
    synoptic_weather_overview: str = Field(..., description="Synoptic atmospheric summary from IMD Kolkata")
    crop_advisory: AgrometBulletinCropAdvisory = Field(..., description="Selected crop advisory dossier")
    issuing_bodies: List[str] = Field(..., description="Co-issuing organizations")
    last_fetched: str = Field(..., description="Live fetch timestamp")
    is_live_synchronized: bool = Field(True, description="True if synchronized with live IMD/GKMS pipeline")


class CoarseCoordinate(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")


class ForecastResponse(BaseModel):
    panchayat_id: str = Field(..., description="Target Panchayat Identifier")
    panchayat_name: str = Field(..., description="Official Gram Panchayat Name")
    gp_code: Optional[int] = Field(None, description="Local Government Directory (LGD) Gram Panchayat Code")
    latitude: Optional[float] = Field(None, description="Exact Gram Panchayat latitude")
    longitude: Optional[float] = Field(None, description="Exact Gram Panchayat longitude")
    panchayat_lat: Optional[float] = Field(None, description="Backward-compatible GP latitude alias")
    panchayat_lon: Optional[float] = Field(None, description="Backward-compatible GP longitude alias")
    elevation_m: Optional[float] = Field(None, description="30m SRTM DEM elevation in meters")
    soil_type: Optional[str] = Field(None, description="Calibrated agricultural soil classification")
    nearest_river: Optional[str] = Field(None, description="Name of nearest hydrological river corridor")
    distance_to_river_m: Optional[float] = Field(None, description="Geodesic distance to nearest river in meters")
    block_name: Optional[str] = Field(None, description="CD Block Name")
    district_name: Optional[str] = Field(None, description="District Name")
    crop: str = Field(..., description="Active crop context")
    issued_at: Optional[str] = Field(None, description="ISO timestamp of forecast generation")
    model_version: str = Field(..., description="Downscaling ML model release")
    rainfall_model: str = Field(..., description="Rainfall methodology")
    is_live_dynamic: bool = Field(..., description="True if using live ECMWF/GFS stream")
    source: str = Field(..., description="Data lineage and provider")
    coarse_coordinate: CoarseCoordinate = Field(..., description="Grid centroid coordinate")
    grid_distance_km: Optional[float] = Field(None, description="Distance offset between regional NWP grid centroid and local GP micro-terrain in km")
    forecast: List[DailyForecast] = Field(..., description="5-day downscaled forecast horizon")
    advisories: List[AdvisorySummaryItem] = Field(..., description="Active agricultural advisories")
    live_agromet_bulletin: Optional[AgrometBulletinResponse] = Field(None, description="Live official Agromet Advisory Bulletin from required authoritative source")
    live_weather: Optional[LiveWeatherPayload] = Field(None, description="24-hour hourly weather and operational spraying telemetry")
    phenology: Optional[Dict[str, Any]] = Field(None, description="Dynamic crop growth phenology state")
    seasonal_info: Optional[Dict[str, Any]] = Field(None, description="Agricultural season, auto-selected crop, and seasonal activity metadata")
    agro_climatic_zone: Optional[str] = Field(None, description="Agro-Climatic Zone (Delta / Laterite / Terai)")
    astronomy: Optional[Dict[str, Any]] = Field(None, description="Sun and Moon astronomical ephemeris")
    air_quality: Optional[Dict[str, Any]] = Field(None, description="Air Quality Index and particulate sub-indices")
    multi_model_ensemble: Optional[Dict[str, Any]] = Field(None, description="Multi-model comparison spread (TerraMind, ECMWF, GFS, ICON)")
    degraded: bool = Field(False, description="Degraded mode indicator")
    degraded_reason: Optional[str] = Field(None, description="Explanation when running in degraded fallback mode")


# ============================================================
# AI AGRO-CLIMATIC CHATBOT SCHEMAS
# ============================================================

class AIChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant' or 'system'")
    content: str = Field(..., description="Message text")


class AIChatContext(BaseModel):
    panchayat_id: Optional[str] = Field(None, description="Current Gram Panchayat ID")
    panchayat_name: Optional[str] = Field(None, description="Gram Panchayat Name")
    block_name: Optional[str] = Field(None, description="CD Block Name")
    district_name: Optional[str] = Field(None, description="District Name")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    elevation_m: Optional[float] = Field(None, description="Elevation AMSL in meters")
    soil_type: Optional[str] = Field(None, description="Soil classification (sandy/non_sandy)")
    distance_to_river_km: Optional[float] = Field(None, description="Distance to nearest river corridor in km")
    crop: Optional[str] = Field("paddy", description="Selected crop context")
    crop_stage: Optional[str] = Field(None, description="Current crop growth phase")
    today_weather: Optional[Dict[str, Any]] = Field(None, description="Current/today weather variables")
    forecast_summary: Optional[List[Dict[str, Any]]] = Field(None, description="5-day downscaled forecast summary")
    advisories: Optional[List[Dict[str, Any]]] = Field(None, description="Active agronomic advisories with source")
    cyclone_alert: Optional[Dict[str, Any]] = Field(None, description="Live cyclone/disturbance intelligence")


class AIChatRequest(BaseModel):
    message: str = Field(..., description="User question or agricultural inquiry")
    conversation_history: List[AIChatMessage] = Field(default_factory=list, description="Prior conversation messages")
    context: Optional[AIChatContext] = Field(None, description="Real-time Gram Panchayat and weather context")


class AIChatResponse(BaseModel):
    reply: str = Field(..., description="AI response text formatted in Markdown")
    sources: List[str] = Field(default_factory=list, description="Authoritative sources and models referenced")
    action_items: List[str] = Field(default_factory=list, description="Structured actionable operational steps")
    suggested_questions: List[str] = Field(default_factory=list, description="Context-relevant follow-up prompts")
    engine: str = Field("terramind_expert", description="Inference engine utilized: 'gemini' or 'terramind_expert'")


# ============================================================
# CROP ADVISORY DOSSIER SCHEMAS
# ============================================================

class CropAdvisoryDossierResponse(BaseModel):
    crop: str = Field(..., description="Target agricultural crop")
    panchayat_id: str = Field(..., description="Gram Panchayat ID")
    generated_at: str = Field(..., description="ISO generation timestamp")
    phenology_summary: Dict[str, Any] = Field(..., description="Crop phenology, active stage, and GDD metrics")
    package_of_practices: List[Dict[str, Any]] = Field(..., description="Stage-wise cultural operations from seed to harvest")
    pest_and_disease_doctor: List[Dict[str, Any]] = Field(..., description="Diagnostic catalog with symptoms, chemical dosage, and bio-control")
    fertilizer_calculator: Dict[str, Any] = Field(..., description="Commercial NPK fertilizer calculations for field area")
    spray_advisor: Dict[str, Any] = Field(..., description="Agrochemical spray window safety rating, Delta-T, and tank-mixing rules")
    water_irrigation_budget: Dict[str, Any] = Field(..., description="FAO-56 reference ET0, crop ETc, and net irrigation requirement")
    mandi_market_intelligence: Dict[str, Any] = Field(..., description="APMC mandi price benchmarks, trends, and storage criteria")

