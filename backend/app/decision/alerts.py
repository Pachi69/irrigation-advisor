"""Deteccion de alertas climaticas criticas desde el pronostico.

Umbrales para la zona de San Rafael, Mendoza:
    - Helada: temp_min <= 2°C (margen de seguridad pre-cero)
    - Ola de calor: temp_max >= 38°C
    
Pendiente: Deteccion de granizo requiere weathercode de Open-Meteo.
"""

from app.schemas.climate import ForecastDay
from app.models.alert import Alert, AlertType

FROST_THRESHOLD_C = 2.0
HEAT_WAVE_THRESHOLD_C = 38.0


def check_climate_alerts(field_id: int, forecast: list[ForecastDay]) -> list[Alert]:
    """Evalua el pronostico y retorna alertas ante condiciones criticas.
    Args:
        field_id: ID del campo a evaluar.
        forecast: lista de dias de pronostico.

    Returns:
        Lista de Alert sin persistir. Puede estar vacia si no hay condiciones criticas.
    """
    alerts = []
    for day in forecast:
        if day.temp_min_c <= FROST_THRESHOLD_C:
            alerts.append(Alert(
                field_id=field_id,
                type=AlertType.frost,
                message=(
                    f"Helada prevista para el {day.date}: "
                    f"temperatura minima de {day.temp_min_c:.1f}°C."
                ), 
                date=day.date,
                sent=False
            ))
        if day.temp_max_c >= HEAT_WAVE_THRESHOLD_C:
            alerts.append(Alert(
                field_id=field_id,
                type=AlertType.heat_wave,
                message=(
                    f"Ola de calor prevista para el {day.date}: "
                    f"temperatura maxima de {day.temp_max_c:.1f}°C."
                ), 
                date=day.date,
                sent=False
            ))
    return alerts