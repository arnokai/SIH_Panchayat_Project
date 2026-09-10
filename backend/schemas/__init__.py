"""
TerraMind API Schemas Package
"""

from backend.schemas.models import (
    RootResponse,
    HealthResponse,
    PanchayatBrief,
    PanchayatListResponse,
    DistrictSummary,
    StatewideDistrictsResponse,
    StatewidePanchayatsResponse,
    StatewideStatsResponse,
    QuantileRain,
    TMaxObj,
    AdvisoryDetail,
    AdvisorySummaryItem,
    DailyForecast,
    CurrentWeather,
    HourlyRecord,
    HourlyWeather,
    OperationalRefinement,
    LiveWeatherPayload,
    CoarseCoordinate,
    ForecastResponse,
)

__all__ = [
    "RootResponse",
    "HealthResponse",
    "PanchayatBrief",
    "PanchayatListResponse",
    "DistrictSummary",
    "StatewideDistrictsResponse",
    "StatewidePanchayatsResponse",
    "StatewideStatsResponse",
    "QuantileRain",
    "TMaxObj",
    "AdvisoryDetail",
    "AdvisorySummaryItem",
    "DailyForecast",
    "CurrentWeather",
    "HourlyRecord",
    "HourlyWeather",
    "OperationalRefinement",
    "LiveWeatherPayload",
    "CoarseCoordinate",
    "ForecastResponse",
]
