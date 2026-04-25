"""Job diario de generacion de recomendaciones de riego.

Se ejecuta a las 22:00 hs (hora Mendoza) para todos los campos activos.
"""
import logging
from app.database import SessionLocal
from app.models.field import Field as FieldModel, FieldStatus
from app.services.recommendation import run_recommendation_pipeline

logger = logging.getLogger(__name__)

def generate_daily_recommendations() -> None:
    """Genera y persiste recomendaciones para todos los campos activos."""
    db = SessionLocal()
    try:
        fields = (
            db.query(FieldModel)
            .filter(FieldModel.status == FieldStatus.active)
            .all()
        )
        logger.info("Job diario: procesado %d campos activos", len(fields))
        ok = errors = 0
        for field in fields:
            try:
                run_recommendation_pipeline(field, db)
                ok += 1
            except Exception as e:
                logger.error("Error procesando campo %d: %s", field.id, e)
                errors += 1
        logger.info("Job diario completado - ok: %d, errores: %d", ok, errors)
    finally:
        db.close()