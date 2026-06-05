from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import UrgencyLevel


class IrrigationConfirmationCreate(BaseModel):
    """Datos que envia el productor al confirmar un riego (en tiempo de riego)
    Se confirma por tiempo (si el sector tiene caudal cargado) o por volumen (m3).
    """
    irrigation_date: date
    applied_time_min: Optional[float] = Field(default=None, gt=0)
    applied_volume_m3: Optional[float] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _exactly_one(self):
        if (self.applied_time_min is None) == (self.applied_volume_m3 is None):
            raise ValueError("Indica el riego por tiempo o por volumen, uno solo.")
        return self


class PendingConfirmationItem(BaseModel):
    """Recomendacion accionable (mm > 0) que aun no fue confirmada"""
    recommendation_id: int
    date: date
    recommended_irrigation_mm: float
    time_min: Optional[float] = None
    volume_m3: Optional[float] = None
    urgency: UrgencyLevel
    water_deficit_mm: float

    model_config = {"from_attributes": True}


class IrrigationConfirmationResponse(BaseModel):
    """Confirmacion de riego persistida"""
    id: int
    recommendation_id: int
    sector_id: int
    irrigation_date: date
    applied_irrigation_mm: float
    created_at: datetime

    model_config = {"from_attributes": True}