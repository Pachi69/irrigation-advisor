from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, func, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import CropType, HailNetType, IrrigationType, SectorStatus


class Sector(Base):
    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[SectorStatus] = mapped_column(Enum(SectorStatus), nullable=False, default=SectorStatus.pending)

    # Identidad del sector
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    crop_type: Mapped[CropType] = mapped_column(Enum(CropType), nullable=False)
    variety: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Geometría
    area_ha: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    polygon_geojson: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Riego
    irrigation_type: Mapped[IrrigationType] = mapped_column(Enum(IrrigationType), nullable=False, default=IrrigationType.aspersion)
    # Caudal del sistema (caudal de la bomba / area).
    # sin el no se calcula el tiempo de riego.
    flow_rate_ls_ha: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Malla antigranizo
    hail_net_type: Mapped[HailNetType] = mapped_column(Enum(HailNetType), nullable=False, default=HailNetType.none)

    # Preferencias de notificación
    notification_frequency_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notification_hour: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    last_notification_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Estado del balance hídrico
    last_saturation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_deficit_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_deficit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relaciones
    field: Mapped["Field"] = relationship(back_populates="sectors")
    satellite_records: Mapped[list["SatelliteRecord"]] = relationship(back_populates="sector", cascade="all, delete-orphan", passive_deletes=True)
    water_balances: Mapped[list["DailyWaterBalance"]] = relationship(back_populates="sector", cascade="all, delete-orphan", passive_deletes=True)
    irrigation_confirmations: Mapped[list["IrrigationConfirmation"]] = relationship(back_populates="sector", cascade="all, delete-orphan", passive_deletes=True)