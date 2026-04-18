import enum 
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class CropType(enum.Enum):
    vine = "vine"
    peach = "peach"

class IrrigationType(enum.Enum):
    drip = "drip"
    sprinkler = "sprinkler"
    flood = "flood"

class SoilType(enum.Enum):
    sandy = "sandy"
    clay = "clay"
    loamy = "loamy"

class FieldStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"

class Field(Base):
    __tablename__ = "fields"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    crop_type: Mapped[CropType] = mapped_column(Enum(CropType), nullable=False)
    area_ha: Mapped[float] = mapped_column(Float, nullable=False)
    irrigation_type: Mapped[IrrigationType] = mapped_column(Enum(IrrigationType), nullable=False)
    soil_type: Mapped[SoilType] = mapped_column(Enum(SoilType), nullable=False)
    status: Mapped[FieldStatus] = mapped_column(Enum(FieldStatus), nullable=False, default=FieldStatus.pending)
    polygon_geojson: Mapped[dict] = mapped_column(JSON, nullable=False)
    elevation_m: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    has_hail_net: Mapped[bool] = mapped_column(Boolean, default=False)
    planting_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="fields")
    soil: Mapped["Soil"] = relationship(back_populates="field", uselist=False)
    satellite_records: Mapped[list["SatelliteRecord"]] = relationship(back_populates="field", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="field", cascade="all, delete-orphan")
    irrigation_confirmations: Mapped[list["IrrigationConfirmation"]] = relationship(back_populates="field", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="field", cascade="all, delete-orphan")