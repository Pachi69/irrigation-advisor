"""Job de envio de notificaciones push de recomendaciones diarias.

Corre cada hora (hora Mendoza). Por cada sector activo notifica solo si:
    - La hora elegida del sector coincide con la hora actual,
    - Se cumplio su frecuencia (hoy - ultima_notificacion >= frecuencia_dias),
    - La recomendacion de ayer tiene lamina > 0.

El calculo de la recomendacion va en otro job (00:01); aca solo se notifica.
"""
import logging
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

from app.database import SessionLocal
from app.models.daily_water_balance import DailyWaterBalance
from app.services.push import send_push_to_user
from app.api._helpers import iter_active_sectors

logger = logging.getLogger(__name__)

MENDOZA_TZ = ZoneInfo("America/Argentina/Mendoza")
DEFAULT_NOTIFICATION_HOUR = 8 # Sector sin hora elegida

URGENCY_LABELS = {
    "low": "Baja",
    "medium": "Media",
    "high": "Alta",
    "critical": "Critica",
}

def _frequency_due(sector, today: date) -> bool:
    """True si paso suficiente tiempo desde la ultima notificacion."""
    if sector.last_notification_date is None:
        return True
    return (today - sector.last_notification_date).days >= sector.notification_frequency_days

def _format_minutes(total_min: float) -> str:
    """Minutos -> 'X h Y min" legible."""
    total = int(round(total_min))
    h, m = divmod(total, 60)
    if h and m:
        return f"{h} h {m} min"
    if h:
        return f"{h} h"
    return f"{m} min"

def _amount_text(rec) -> str:
    """Cantidad a regar segun la unidad disponioble (mismo criterio que el front).
    
    Con caudal (time_min) -> tiempo de riego; sin caudal -> volumen (m3);
    fallback a lamina (mm).
    """
    mm = rec.recommended_irrigation_mm
    if rec.time_min is not None:
        return f"{_format_minutes(rec.time_min)} de riego"
    if rec.volume_m3 is not None:
        return f"{rec.volume_m3:.1f} m³"
    return f"{mm:.1f} mm"


def send_daily_recommendation_notifications() -> None:
    """Envia push con la recomendacion del dia a cada sector segun su hora y frecuencia."""
    db = SessionLocal()
    today = date.today()
    target_date = date.today() - timedelta(days=1)  # La recomendacion se genera a las 00:00, asi que es para el dia anterior
    current_hour = datetime.now(MENDOZA_TZ).hour
    try:
        sectors = iter_active_sectors(db)
        ok = off_hour = not_due = no_rec = zero_mm = not_sent = errors = 0

        for sector in sectors:
            try:
                hour = sector.notification_hour.hour if sector.notification_hour else DEFAULT_NOTIFICATION_HOUR
                if hour != current_hour:
                    off_hour += 1
                    continue
                if not _frequency_due(sector, today):
                    not_due += 1
                    continue

                wb = (
                    db.query(DailyWaterBalance)
                    .filter(
                        DailyWaterBalance.sector_id == sector.id,
                        DailyWaterBalance.date == target_date,
                    )
                    .first()
                )
                if not wb or not wb.recommendation:
                    no_rec += 1
                    continue

                rec = wb.recommendation
                if rec.recommended_irrigation_mm <= 0:
                    zero_mm += 1
                    continue

                urgency_label = URGENCY_LABELS.get(rec.urgency.value, rec.urgency.value)
                sent = send_push_to_user(
                    user_id=sector.field.user_id,
                    title=f"Riego - {sector.field.name} / {sector.name}",
                    body=f"Regar {_amount_text(rec)} - Urgencia: {urgency_label}",
                    db=db,
                )
                if sent:
                    sector.last_notification_date = today
                    db.commit()
                    ok += 1
                else:
                    not_sent += 1

            except Exception as e:
                logger.error("Error enviando notificacion sector %d: %s", sector.id, e)
                errors += 1

        logger.info(
            "Job notificaciones [hora %02d] - ok: %d fuera_hora: %d sin_frecuencia: %d sin_rec: %d lamina0: %d sin envio: %d err: %d",
            current_hour, ok, off_hour, not_due, no_rec, zero_mm, not_sent, errors,
        )
    
    finally:
        db.close()