from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, func, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class IrrigationConfirmation(Base):
    __tablename__ = "irrigation_confirmations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("recommendations.id"), nullable=False, index=True, unique=True)
    field_id: Mapped[int] = mapped_column(ForeignKey("fields.id"), nullable=False, index=True)
    irrigation_date: Mapped[date] = mapped_column(Date, nullable=False)
    applied_irrigation_mm: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    recommendation: Mapped["Recommendation"] = relationship(back_populates="irrigation_confirmation")
    field: Mapped["Field"] = relationship(back_populates="irrigation_confirmations")