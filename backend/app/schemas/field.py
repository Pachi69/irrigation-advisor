from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import SoilType, FieldStatus
from app.schemas.sector import SectorPublic


class FieldCreate(BaseModel):
    """Lo que el productor envía al registrar un campo"""
    name: str = Field(min_length=2, max_length=255)

class FieldPublic(BaseModel):
    """Lo que la API devuelve al cliente"""
    id: int
    name: str
    soil_type: SoilType | None = None
    status: FieldStatus
    elevation_m: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime
    sectors: list[SectorPublic] = []

    model_config = ConfigDict(from_attributes=True)


class FieldUpdate(BaseModel):
    """ Campos editables por el productor. Todos opcionales - solo se actualizan los enviados."""
    name: str | None = Field(default=None, min_length=2, max_length=255)