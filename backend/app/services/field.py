from datetime import date as DateType, timedelta

import logging

from sqlalchemy.orm import Session

from app.models.field import Field as FieldModel
from app.services.recommendation import run_backfill, run_recommendation_pipeline


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

    # Backfill desde el dia siguiente al evento de saturacion
    field.last_deficit_mm = 0.0
    field.last_deficit_date = saturation
    db.flush()

    run_backfill(field, saturation + timedelta(days=1), today - timedelta(days=1), db)
    db.commit()
    logger.info(
        "Init balance campo %d: backfill desde %s (deficit final %.1f mm)",
        field.id, saturation, field.last_deficit_mm or 0.0,
    )

    # Re-ejecutar pipeline live para que "ayer" quede con urgencia y confianza reales
    try:
        run_recommendation_pipeline(field, db)
    except Exception as e:
        logger.warning(
            "No se pudo re-ejecutar pipeline live al final de init: %s. "
            "La recomendacion de ayer queda con valores de backfill.", e,
        )