from app.schemas.climate import ClimateData, ForecastDay
from app.models.alert import Alert


def check_climate_alerts(
    field_id: int,
    climate: ClimateData,
    forecast: list[ForecastDay],
) -> list[Alert]:
    raise NotImplementedError