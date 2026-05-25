from datetime import date as DateType, timedelta

import logging

from sqlalchemy.orm import Session

from app.models.field import Field as FieldModel
from app.services.recommendation import recompute_balance_from


logger = logging.getLogger(__name__)


def initialize_water_balance(field: FieldModel, db: Session) -> None:
    """Inicializa el balance hidrico de un campo recien aprobado.

    Estrategia (FAO-56 Sec. 8.4.2 'Initial depletion'):
    - Si el productor declaro last_saturation_date < hoy:
        asume Dr=0 ese dia y aplica Ec.82 hacia adelante hasta ayer.
    - Si declaro last_saturation_date == hoy (o None):
        no hace backfill; asume Dr=0 hoy (campo recien saturado).
    """
    today = DateType.today()
    saturation = field.last_saturation_date

    if saturation is None or saturation >= today:
        field.last_deficit_mm = 0.0
        field.last_deficit_date = today
        db.commit()
        logger.info("Init balance campo %d: sin backfill (Dr=0 hoy)", field.id)
        return

    # Suelo saturado en last_saturation_date (Dr=0) -> recalcular desde el dia siguiente
    recompute_balance_from(field, saturation + timedelta(days=1), 0.0, db)
    logger.info(
        "Init balance campo %d: recalculo desde %s (deficit final %.1f mm)",
        field.id, saturation, field.last_deficit_mm or 0.0,
    )