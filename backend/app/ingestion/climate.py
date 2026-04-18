from datetime import date
from app.schemas.climate import ClimateData, ForecastDay


def get_climate_data(latitude: float, longitude: float, target_date: date) -> ClimateData:
    raise NotImplementedError

def get_forecast(latitude: float, longitude: float, days: int = 5) -> list[ForecastDay]:
    raise NotImplementedError