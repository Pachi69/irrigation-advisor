"""Job de deteccion de alertas climaticas criticas.
Se ejecuta cada 6 horas para todos los campos activos.
"""
import logging
from app.database import SessionLocal
from app.models.field import Field as FieldModel, FieldStatus
from app.models.alert import Alert
from app.ingestion.climate import get_forecast
from app.decision.alerts import check_climate_alerts

logger = logging.getLogger(__name__)

FORECAST_DAYS = 5


def generate_climate_alerts() -> None:
    """Detecta y persiste alertas climaticas criticas para todos los campos activos."""
    db = SessionLocal()
    try:
        fields = (
            db.query(FieldModel)
            .filter(FieldModel.status == FieldStatus.active)
            .all()
        )
        logger.info("Job alertas: procesando %d campos activos", len(fields))
        ok = errors = 0
        for field in fields:
            try:
                forecast = get_forecast(field.latitude, field.longitude, days=FORECAST_DAYS)
                new_alerts = check_climate_alerts(field.id, forecast)
                for alert in new_alerts:
                    # Evitar duplicados: no insertar si ya existe alerta del mismo tipo y fecha
                    exists = (
                        db.query(Alert)
                        .filter(
                            Alert.field_id == field.id,
                            Alert.type == alert.type,
                            Alert.date == alert.date,
                        )
                        .first()
                    )
                    if not exists:
                        db.add(alert)
                        logger.info(
                            "Alerta generada - campo %d tipo %s fecha %s",
                            field.id, alert.type, alert.date
                        )
                db.commit()
                ok += 1
            except Exception as e:
                logger.error("Error procesando alertas campo %d: %s", field.id, e)
                errors += 1
        logger.info("Job alertas completado - ok: %d, errores: %d", ok, errors)
    finally:
        db.close()