from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import UrgencyLevel


class IrrigationConfirmationCreate(BaseModel):
    """Datos que envia el productor al confirmar un riego."""
    irrigation_date: date
    applied_irrigation_mm: float = Field(gt=0)


class PendingConfirmationItem(BaseModel):
    """Recomendacion accionable (mm > 0) que aun no fue confirmada"""
    recommendation_id: int
    date: date
    recommended_irrigation_mm: float
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