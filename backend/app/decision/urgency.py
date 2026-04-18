from app.schemas.calculation import WaterBalanceResult, UrgencyResult
from app.schemas.climate import ForecastDay


def calculate_urgency(
    balance: WaterBalanceResult,
    forecast: list[ForecastDay],
) -> UrgencyResult:
    raise NotImplementedError