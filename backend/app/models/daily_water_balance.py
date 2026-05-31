from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import KcSource, PhenologicalStage


class DailyWaterBalance(Base):
    __tablename__ = "daily_water_balances"
    __table_args__ = (
        UniqueConstraint("sector_id", "date", name="uq_balance_sector_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    eto_mm: Mapped[float] = mapped_column(Float, nullable=False)
    kc: Mapped[float] = mapped_column(Float, nullable=False)
    kc_source: Mapped[KcSource] = mapped_column(Enum(KcSource), nullable=False)
    etc_mm: Mapped[float] = mapped_column(Float, nullable=False)
    water_deficit_mm: Mapped[float] = mapped_column(Float, nullable=False)
    ks: Mapped[float] = mapped_column(Float, nullable=False)
    phenological_stage: Mapped[PhenologicalStage] = mapped_column(Enum(PhenologicalStage), nullable=False)
    precipitation_mm: Mapped[float] = mapped_column(Float, nullable=False)
    taw_mm: Mapped[float] = mapped_column(Float, nullable=False)
    raw_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ndvi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ndvi_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sector: Mapped["Sector"] = relationship(back_populates="water_balances")
    recommendation: Mapped[Optional["Recommendation"]] = relationship(
        back_populates="water_balance", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )