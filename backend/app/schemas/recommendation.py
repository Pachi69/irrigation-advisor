from datetime import date
from pydantic import BaseModel, Field
from app.models.enums import UrgencyLevel, ConfidenceLevel, KcSource, PhenologicalStage


class RecommendationResponse(BaseModel):
    """Respuesta completa de la recomendacion de riego para un campo."""
    sector_id: int
    date: date

    # Resultado final
    urgency_level: UrgencyLevel = Field(validation_alias='urgency')
    recommended_irrigation_mm: float
    volume_m3: float | None = None
    time_min: float | None = None
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
    cloud_cover_pct: float | None = None

    # Clima del dia usado para la recomendacion
    temp_max_c: float | None = None
    temp_min_c: float | None = None
    temp_mean_c: float | None = None
    humidity_pct: float | None = None
    wind_speed_ms: float | None = None
    solar_radiation_mj: float | None = None
    pressure_kpa: float | None = None
    precipitation_mm: float | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class RecommendationHistoryItem(BaseModel):
    """Item del historial de recomendaciones de un campo."""
    id: int
    date: date
    urgency: UrgencyLevel
    recommended_irrigation_mm: float
    volume_m3: float | None = None
    time_min: float | None = None
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