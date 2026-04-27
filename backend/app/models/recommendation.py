import enum
from datetime import datetime, date

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class KcSource(enum.Enum):
    s2_dynamic = "s2_dynamic"
    tabular = "tabular"

class PhenologicalStage(enum.Enum):
    initial = "initial"
    development = "development"
    mid = "mid"
    late = "late"

class UrgencyLevel(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class ConfidenceLevel(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    eto_mm: Mapped[float] = mapped_column(Float, nullable=False)
    kc: Mapped[float] = mapped_column(Float, nullable=False)
    kc_source: Mapped[KcSource] = mapped_column(Enum(KcSource), nullable=False)
    etc_mm: Mapped[float] = mapped_column(Float, nullable=False)
    water_deficit_mm: Mapped[float] = mapped_column(Float, nullable=False)
    ks: Mapped[float] = mapped_column(Float, nullable=False)
    phenological_stage: Mapped[PhenologicalStage] = mapped_column(Enum(PhenologicalStage), nullable=False)
    recommended_irrigation_mm: Mapped[float] = mapped_column(Float, nullable=False)
    urgency: Mapped[UrgencyLevel] = mapped_column(Enum(UrgencyLevel), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    precipitation_mm: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[ConfidenceLevel] = mapped_column(Enum(ConfidenceLevel), nullable=False)
    taw_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    ndvi: Mapped[float | None] = mapped_column(Float, nullable=True)
    ndvi_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    field: Mapped["Field"] = relationship(back_populates="recommendations")
    irrigation_confirmation: Mapped["IrrigationConfirmation"] = relationship(back_populates="recommendation", uselist=False)