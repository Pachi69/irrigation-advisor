"""Job de envio de notificaciones push de recomendaciones diarias.

Se ejecuta a las 08:00 hs (hora Mendoza). Busca la recomendacion generada
esta madrugada para cada sector y envia la notificacion push al productor.
"""
import logging
from datetime import date, timedelta

from app.database import SessionLocal
from app.models.daily_water_balance import DailyWaterBalance
from app.services.push import send_push_to_user
from app.api._helpers import iter_active_sectors

logger = logging.getLogger(__name__)

URGENCY_LABELS = {
    "low": "Baja",
    "medium": "Media",
    "high": "Alta",
    "critical": "Critica",
}


def send_daily_recommendation_notifications() -> None:
    """Envia push con la recomendacion de reigo del dia a cada productor, por sector."""
    db = SessionLocal()
    target_date = date.today() - timedelta(days=1)  # La recomendacion se genera a las 00:00, asi que es para el dia anterior
    try:
        sectors = iter_active_sectors(db)
        logger.info("Job notificaciones: procesando %d sectores activos", len(sectors))
        ok = no_recommendation = not_sent = errors = 0

        for sector in sectors:
            try:
                wb = (
                    db.query(DailyWaterBalance)
                    .filter(
                        DailyWaterBalance.sector_id == sector.id,
                        DailyWaterBalance.date == target_date,
                    )
                    .first()
                )
                if not wb or not wb.recommendation:
                    no_recommendation += 1
                    continue

                rec = wb.recommendation
                urgency_label = URGENCY_LABELS.get(rec.urgency.value, rec.urgency.value)
                sent = send_push_to_user(
                    user_id=sector.field.user_id,
                    title=f"Riego - {sector.field.name} / {sector.name}",
                    body=f"Lamina recomendada: {rec.recommended_irrigation_mm:.1f} mm - Urgencia: {urgency_label}",
                    db=db,
                )
                if sent:
                    ok += 1
                else:
                    not_sent += 1

            except Exception as e:
                logger.error("Error enviando notificacion sector %d: %s", sector.id, e)
                errors += 1

        logger.info(
            "Job notificaciones completado - ok: %d, sin recomendacion: %d, sin envio: %d, errores: %d",
            ok, no_recommendation, not_sent, errors,
        )
    
    finally:
        db.close()