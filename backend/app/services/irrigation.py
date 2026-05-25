"""Servicio de confirmacion de riego: persiste el riego aplicado y recalcula el balance."""
from datetime import date as DateType, timedelta

import logging

from sqlalchemy.orm import Session

from app.models.field import Field as FieldModel
from app.models.recommendation import Recommendation
from app.models.daily_water_balance import DailyWaterBalance
from app.models.irrigation_confirmation import IrrigationConfirmation
from app.services.recommendation import recompute_balance_from

logger = logging.getLogger(__name__)


def confirm_irrigation(
    field: FieldModel,
    recommendation: Recommendation,
    irrigation_date: DateType,
    applied_mm: float,
    db: Session,
) -> IrrigationConfirmation:
    """Crea la confirmacion de riego y recalcula el balance desde la fecha de riego."""
    confirmation = IrrigationConfirmation(
        recommendation_id=recommendation.id,
        field_id=field.id,
        irrigation_date=irrigation_date,
        applied_irrigation_mm=applied_mm,
    )
    db.add(confirmation)
    db.flush()

    # Semilla: deficit al final del dia anterior a la fecha de riego
    prev_wb = (
        db.query(DailyWaterBalance)
        .filter(
            DailyWaterBalance.field_id == field.id,
            DailyWaterBalance.date < irrigation_date,
        )
        .order_by(DailyWaterBalance.date.desc())
        .first()
    )
    seed = prev_wb.water_deficit_mm if prev_wb else 0.0

    recompute_balance_from(field, irrigation_date, seed, db)

    db.refresh(confirmation)
    return confirmation