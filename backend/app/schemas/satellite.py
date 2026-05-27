from datetime import date
from pydantic import BaseModel


class SatelliteData(BaseModel):
    field_id: int
    date: date
    ndvi: float | None = None
    cloud_cover_pct: float | None = None
    