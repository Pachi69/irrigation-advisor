from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SoilType

class Field(Base):
    __tablename__ = "fields"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    soil_type: Mapped[SoilType | None] = mapped_column(Enum(SoilType), nullable=True)
    elevation_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="fields")
    sectors: Mapped[list["Sector"]] = relationship(back_populates="field", cascade="all, delete-orphan", passive_deletes=True)
    alerts: Mapped[list["Alert"]] = relationship(back_populates="field", cascade="all, delete-orphan", passive_deletes=True)