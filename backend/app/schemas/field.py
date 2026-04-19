from datetime import date, datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.field import CropType, IrrigationType, SoilType, FieldStatus

class FieldCreate(BaseModel):
    """Lo que el productor envía al registrar un campo"""
    name: str = Field(min_length=2, max_length=255)
    crop_type: CropType
    area_ha: float = Field(gt=0, le=10000)
    irrigation_type: IrrigationType
    soil_type: SoilType
    has_hail_net: bool = False
    planting_date: date

class FieldPublic(BaseModel):
    """Lo que la API devuelve al cliente"""
    id: int
    name: str
    crop_type: CropType
    area_ha: float
    irrigation_type: IrrigationType
    soil_type: SoilType
    has_hail_net: bool
    planting_date: date
    status: FieldStatus
    polygon_geojson: dict | None = None
    elevation_m: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)