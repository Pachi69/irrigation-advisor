import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import CropType, IrrigationType, SoilType, FieldStatus

class Field(Base):
    __tablename__ = "fields"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    crop_type: Mapped[CropType] = mapped_column(Enum(CropType), nullable=False)
    area_ha: Mapped[Optional[float]] = mapped_column(Float, nullable=False)
    irrigation_type: Mapped[IrrigationType] = mapped_column(Enum(IrrigationType), nullable=False)
    soil_type: Mapped[SoilType] = mapped_column(Enum(SoilType), nullable=False)
    status: Mapped[FieldStatus] = mapped_column(Enum(FieldStatus), nullable=False, default=FieldStatus.pending)
    polygon_geojson: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    elevation_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_deficit_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_deficit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    has_hail_net: Mapped[bool] = mapped_column(Boolean, default=False)
    planting_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_saturation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="fields")
    satellite_records: Mapped[list["SatelliteRecord"]] = relationship(back_populates="field", cascade="all, delete-orphan", passive_deletes=True)
    water_balances: Mapped[list["DailyWaterBalance"]] = relationship(back_populates="field", cascade="all, delete-orphan", passive_deletes=True)
    irrigation_confirmations: Mapped[list["IrrigationConfirmation"]] = relationship(back_populates="field", cascade="all, delete-orphan", passive_deletes=True)
    alerts: Mapped[list["Alert"]] = relationship(back_populates="field", cascade="all, delete-orphan", passive_deletes=True)