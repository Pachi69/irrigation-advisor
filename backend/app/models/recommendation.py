from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ConfidenceLevel, UrgencyLevel

class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    water_balance_id: Mapped[int] = mapped_column(
        ForeignKey("daily_water_balances.id", ondelete="CASCADE"), nullable=False, unique=True, index=True, 
    )
    recommended_irrigation_mm: Mapped[float] = mapped_column(Float, nullable=False)
    urgency: Mapped[UrgencyLevel] = mapped_column(Enum(UrgencyLevel), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[ConfidenceLevel] = mapped_column(Enum(ConfidenceLevel), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    water_balance: Mapped["DailyWaterBalance"] = relationship(back_populates="recommendation")