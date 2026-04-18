from pydantic import BaseModel
from app.models.recommendation import KcSource, PhenologicalStage, UrgencyLevel, ConfidenceLevel


class EToResult(BaseModel):
    eto_mm: float

class KcResult(BaseModel):
    kc: float
    source: KcSource
    phenological_stage: PhenologicalStage

class WaterBalanceResult(BaseModel):
    water_deficit_mm: float
    ks: float
    taw_mm: float
    raw_mm: float

class UrgencyResult(BaseModel):
    urgency_level: UrgencyLevel
    recommended_irrigation_mm: float
    reason: str
    confidence: ConfidenceLevel