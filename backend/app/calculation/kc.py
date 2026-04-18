from datetime import date
from app.models.field import CropType
from app.schemas.satellite import SatelliteData
from app.schemas.calculation import KcResult


def calculate_kc(
    crop_type: CropType,
    planting_date: date,
    current_date: date,
    satellite_data: SatelliteData | None,
) -> KcResult:
    raise NotImplementedError