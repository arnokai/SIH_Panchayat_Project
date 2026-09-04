from pydantic import BaseModel

class Forecast(BaseModel):
    rainfall_mm: float
    rain_probability: int
    max_temperature: float

class ForecastResponse(BaseModel):
    gp_code: str
    gp_name: str
    forecast: Forecast
    advisory: str
