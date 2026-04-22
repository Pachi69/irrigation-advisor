from datetime import date
from pydantic import BaseModel

class ClimateData(BaseModel):
    date: date
    temp_max_c: float
    temp_min_c: float
    temp_mean_c: float
    humidity_pct: float
    wind_speed_10m: float
    solar_radiation_mj: float
    precipitation_mm: float
    pressure_kpa: float
    eto_reference_mm: float | None = None

class ForecastDay(BaseModel):
    date: date
    temp_max_c: float
    temp_min_c: float
    precipitation_mm: float
    precipitation_probability_pct: float
    eto_reference_mm: float