from app.models.field import SoilType
from app.schemas.calculation import EToResult, KcResult, WaterBalanceResult


def calculate_water_balance(
    eto: EToResult,
    kc: KcResult,
    precipitation_mm: float,
    previous_deficit_mm: float,
    soil_type: SoilType,
    root_depth_m: float,
) -> WaterBalanceResult:
    raise NotImplementedError