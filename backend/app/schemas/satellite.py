from datetime import date
from app.models.satellite_record import SatelliteSource
from pydantic import BaseModel


class SatelliteData(BaseModel):
    field_id: int
    date: date
    source: SatelliteSource
    ndvi: float | None = None
    backscatter_vv: float | None = None
    backscatter_vh: float | None = None
    cloud_cover_pct: float | None = None
    moisture_event_detected: bool = False
    