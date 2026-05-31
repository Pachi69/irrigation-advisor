from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CropType, HailNetType, IrrigationType, UrgencyLevel


class SectorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    crop_type: CropType
    variety: Optional[str] = None
    irrigation_type: IrrigationType = IrrigationType.aspersion
    flow_rate_ls_ha: float = Field(default=1.5, gt=0)
    hail_net_type: HailNetType = HailNetType.none
    notification_frequency_days: int = Field(default=1, ge=1)
    notification_hour: Optional[time] = None
    last_saturation_date: Optional[date] = None
    polygon_geojson: Optional[dict] = None


class SectorUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    variety: Optional[str] = None
    irrigation_type: Optional[IrrigationType] = None
    flow_rate_ls_ha: Optional[float] = Field(default=None, gt=0)
    hail_net_type: Optional[HailNetType] = None
    notification_frequency_days: Optional[int] = Field(default=None, ge=1)
    notification_hour: Optional[time] = None
    last_saturation_date: Optional[date] = None
    polygon_geojson: Optional[dict] = None


class SectorPublic(BaseModel):
    id: int
    field_id: int
    name: str
    crop_type: CropType
    variety: Optional[str] = None
    area_ha: Optional[float] = None
    polygon_geojson: Optional[dict] = None
    irrigation_type: IrrigationType
    flow_rate_ls_ha: float
    hail_net_type: HailNetType
    notification_frequency_days: int
    notification_hour: Optional[time] = None
    last_saturation_date: Optional[date] = None
    last_deficit_mm: Optional[float] = None
    last_recommendation: Optional[LastRecommendationSummary] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LastRecommendationSummary(BaseModel):
    date: date
    urgency: UrgencyLevel
    recommended_irrigation_mm: float
    deficit_pct: float
    deficit_history: list[float]

    model_config = ConfigDict(from_attributes=True)


class DeficitPoint(BaseModel):
    date: date
    pct: float


class NdviPoint(BaseModel):
    date: date
    value: float


class SectorChartData(BaseModel):
    deficit: list[DeficitPoint]
    ndvi: list[NdviPoint]
    raw_threshold_pct: float