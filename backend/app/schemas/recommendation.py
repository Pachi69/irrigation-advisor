from datetime import date
from pydantic import BaseModel, Field
from app.models.recommendation import UrgencyLevel, ConfidenceLevel, KcSource, PhenologicalStage


class RecommendationResponse(BaseModel):
    """Respuesta completa de la recomendacion de riego para un campo."""
    field_id: int
    date: date

    # Resultado final
    urgency_level: UrgencyLevel = Field(validation_alias='urgency')
    recommended_irrigation_mm: float
    reason: str
    confidence: ConfidenceLevel

    # Balance hidrico
    water_deficit_mm: float
    ks: float
    taw_mm: float | None = None
    raw_mm: float | None = None

    # Evapotranspiracion
    eto_mm: float

    # Coeficiente de cultivo
    kc: float
    kc_source: KcSource
    phenological_stage: PhenologicalStage

    # Satelite (None si no hay imagen reciente)
    ndvi: float | None = None
    ndvi_date: date | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class RecommendationHistoryItem(BaseModel):
    """Item del historial de recomendaciones de un campo."""
    id: int
    date: date
    urgency: UrgencyLevel
    recommended_irrigation_mm: float
    reason: str
    confidence: ConfidenceLevel
    water_deficit_mm: float
    taw_mm: float | None = None
    ks: float
    eto_mm: float
    kc: float
    kc_source: KcSource
    phenological_stage: PhenologicalStage

    class Config:
        from_attributes = True