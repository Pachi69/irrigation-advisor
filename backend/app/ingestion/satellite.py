from datetime import date
from app.schemas.satellite import SatelliteData


def get_sentinel2_data(field_id: int, polygon: dict, target_date: date) -> SatelliteData | None:
    raise NotImplementedError


def get_sentinel1_data(field_id: int, polygon: dict, target_date: date) -> SatelliteData | None:
    raise NotImplementedError
