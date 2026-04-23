from datetime import date
from pydantic import BaseModel
from app.models.recommendation import UrgencyLevel, ConfidenceLevel, KcSource, PhenologicalStage


class RecommendationResponse(BaseModel):
    """Respuesta complketa de la recomendacion de riego para un campo."""
    field_id: int
    date: date

    # Resultado final
    urgency_level: UrgencyLevel
    recommended_irrigation_mm: float
    reason: str
    confidence: ConfidenceLevel

    # Balance hidrico
    water_deficit_mm: float
    ks: float
    taw_mm: float
    raw_mm: float

    # Evapotranspiracion
    eto_mm: float

    # Coeficiente de cultivo
    kc: float
    kc_source: KcSource
    phenological_stage: PhenologicalStage

    # Satelite (None si no hay imagen reciente)
    ndvi: float | None = None
    ndvi_date: date | None = None