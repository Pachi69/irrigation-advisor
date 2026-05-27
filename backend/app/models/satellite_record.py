from datetime import datetime, date

from sqlalchemy import Date, DateTime, Float, ForeignKey, func, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class SatelliteRecord(Base):
    __tablename__ = "satellite_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    ndvi: Mapped[float] = mapped_column(Float, nullable=False)
    cloud_cover_pct: Mapped[float] = mapped_column(Float, nullable=False)
    thumbnail_png: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    field: Mapped["Field"] = relationship(back_populates="satellite_records")