"""Job de envio de notificaciones push de recomendaciones diarias.

Se ejecuta a las 08:00 hs (hora Mendoza). Busca la recomendacion generada
esta madrugada y envia la notificacion push al productor.
"""
import logging
from datetime import date, timedelta

from app.database import SessionLocal
from app.models.field import Field as FieldModel, FieldStatus
from app.models.recommendation import Recommendation
from app.services.push import send_push_to_user

logger = logging.getLogger(__name__)

URGENCY_LABELS = {
    "low": "Baja",
    "medium": "Media",
    "high": "Alta",
    "critical": "Critica",
}


def send_daily_recommendation_notifications() -> None:
    """Envia push con la recomendacion de reigo del dia a cada productor."""
    db = SessionLocal()
    target_date = date.today() - timedelta(days=1)  # La recomendacion se genera a las 00:00, asi que es para el dia anterior
    try:
        fields = (
            db.query(FieldModel)
            .filter(FieldModel.status == FieldStatus.active)
            .all()
        )
        logger.info("Job notificaciones: procesando %d campos activos", len(fields))
        ok = skipped = errors = 0

        for field in fields:
            try:
                rec = (
                    db.query(Recommendation)
                    .filter(
                        Recommendation.field_id == field.id,
                        Recommendation.date == target_date,
                    )
                    .first()
                )
                if not rec:
                    logger.info("Campo %d: sin recomendacion para hoy, saltando", field.id, target_date)
                    skipped += 1
                    continue

                urgency_label = URGENCY_LABELS.get(rec.urgency.value, rec.urgency.value)
                sent = send_push_to_user(
                    user_id=field.user_id,
                    title=f"Riego - {field.name}",
                    body=f"Lamina recomendada: {rec.recommended_irrigation_mm:.1f} mm - Urgencia: {urgency_label}",
                    db=db,
                )
                if sent:
                    ok += 1
                else:
                    skipped += 1

            except Exception as e:
                logger.error("Error enviando notificacion campo %d: %s", field.id, e)
                errors += 1

        logger.info("Job notificaciones completado - ok: %d, sin suscripcion: %d, errores: %d", ok, skipped, errors)
    
    finally:
        db.close()