from datetime import date, datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import CropType, SoilType, FieldStatus

class FieldCreate(BaseModel):
    """Lo que el productor envía al registrar un campo"""
    name: str = Field(min_length=2, max_length=255)
    crop_type: CropType
    soil_type: SoilType = SoilType.loam
    has_hail_net: bool = False
    last_saturation_date: date | None = None
    polygon_geojson: dict | None = None

class FieldPublic(BaseModel):
    """Lo que la API devuelve al cliente"""
    id: int
    name: str
    crop_type: CropType
    area_ha: float | None = None
    soil_type: SoilType
    has_hail_net: bool
    last_saturation_date: date | None = None
    status: FieldStatus
    polygon_geojson: dict | None = None
    elevation_m: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FieldUpdate(BaseModel):
    """ Campos editables por el productor. Todos opcionales - solo se actualizan los enviados."""
    name: str | None = Field(default=None, min_length=2, max_length=255)
    crop_type: CropType | None = None
    area_ha: float | None = Field(default=None, gt=0, le=10000)
    soil_type: SoilType | None = None
    has_hail_net: bool | None = None
    last_saturation_date: date | None = None


class DeficitPoint(BaseModel):
    date: date
    pct: float

class NdviPoint(BaseModel):
    date: date
    value: float

class FieldChartData(BaseModel):
    deficit: list[DeficitPoint]
    ndvi: list[NdviPoint]
    raw_threshold_pct: float