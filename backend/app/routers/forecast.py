from fastapi import APIRouter, HTTPException

from app.services.csv_service import get_panchayat_name
from app.services.forecast_service import get_forecast
from app.models.forecast_schema import ForecastResponse

router = APIRouter(prefix="/api/v1", tags=["Forecast"])

@router.get("/forecast/{gp_code}", response_model=ForecastResponse)
def forecast(gp_code: str):

    data = get_forecast(gp_code)
    name = get_panchayat_name(gp_code)

    if not data or not name:
        raise HTTPException(status_code=404, detail="Panchayat not found")

    rainfall, probability, temp = data

    return {
        "gp_code": gp_code,
        "gp_name": name,
        "forecast": {
            "rainfall_mm": rainfall,
            "rain_probability": probability,
            "max_temperature": temp
        },
        "advisory": "Light rain. Safe for fertilizer application."
    }
