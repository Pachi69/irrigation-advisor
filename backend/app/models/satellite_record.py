import enum
from datetime import datetime, date

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class SatelliteSource(enum.Enum):
    sentinel2 = "sentinel2"
    sentinel1 = "sentinel1"

class SatelliteRecord(Base):
    __tablename__ = "satellite_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[SatelliteSource] = mapped_column(Enum(SatelliteSource), nullable=False)
    ndvi: Mapped[float] = mapped_column(Float, nullable=False)
    backscatter_vv: Mapped[float] = mapped_column(Float, nullable=True)
    backscatter_vh: Mapped[float] = mapped_column(Float, nullable=True)
    cloud_cover_pct: Mapped[float] = mapped_column(Float, nullable=False)
    moisture_event_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    field: Mapped["Field"] = relationship(back_populates="satellite_records")