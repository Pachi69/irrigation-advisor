"""Job diario de generacion de recomendaciones de riego.

Se ejecuta a las 00:01 hs (hora Mendoza) para todos los sectores de campos activos.
"""
import logging
from app.database import SessionLocal
from app.services.recommendation import run_recommendation_pipeline
from app.api._helpers import iter_active_fields

logger = logging.getLogger(__name__)

def generate_daily_recommendations() -> None:
    """Genera y persiste recomendaciones para todos los sectores de campos activos."""
    db = SessionLocal()
    try:
        sectors = iter_active_fields(db)
        logger.info("Job diario: procesado %d sectores activos", len(sectors))
        ok = errors = 0
        for sector in sectors:
            try:
                run_recommendation_pipeline(sector, db)
                ok += 1
            except Exception as e:
                logger.error("Error procesando sector %d: %s", sector.id, e)
                errors += 1
        logger.info("Job diario completado - ok: %d, errores: %d", ok, errors)
    finally:
        db.close()