from app.schemas.climate import ClimateData
from app.schemas.calculation import EToResult


def calculate_eto(climate: ClimateData, elevation_m: float) -> EToResult:
    raise NotImplementedError