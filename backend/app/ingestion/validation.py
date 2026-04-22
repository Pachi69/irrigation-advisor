""" Validacion y limpieza de datos climaticos crudos de fuentes externas."""
import logging

logger = logging.getLogger(__name__)

# Rangos fisicos aceptables por variable
# (min_val, max_val) - valores fuera de rango se loguean como advertencias
RANGES: dict[str, tuple[float, float]] = {
    "temp_max_c": (-50.0, 60.0),
    "temp_min_c": (-50.0, 60.0),
    "temp_mean_c": (-50.0, 60.0),
    "humidity_pct": (0.0, 100.0),
    "wind_speed_10m": (0.0, 100.0),
    "solar_radiation_mj": (0.0, 50.0),
    "precipitation_mm": (0.0, 500.0),
    "pressure_kpa": (50.0, 110.0),
    "eto_reference_mm": (0.0, 20.0),
    "precipitation_probability_pct": (0.0, 100.0),
}

# Campos que NO pueden ser null para que el dato sea usable
REQUIRED_FIELDS_CLIMATE = {
    "temp_max_c", "temp_min_c", "temp_mean_c",
    "humidity_pct", "wind_speed_10m",
    "solar_radiation_mj", "precipitation_mm",
}

REQUIRED_FIELDS_FORECAST = {
    "temp_max_c", "temp_min_c", "precipitation_mm"
}

def validate_climate_row (row: dict) -> dict:
    """Valida y limpia un diccionario con los campo de ClimateData.
    
    - Lanza RuntimeError si algun campo requerido es None
    - Loguea advertencia si un valor esta fuera de rango pero lo deja pasar.

    Returns: el mismo dict (puede usarse encadenado)
    """
    for field in REQUIRED_FIELDS_CLIMATE:
        if row.get(field) is None:
            raise RuntimeError(f"Campo requerido '{field}' es null en la respuesta de Open-Meteo")
    
    for field, value in row.items():
        if value is None or field not in RANGES:
            continue
        min_val, max_val = RANGES[field]
        if not (min_val <= value <= max_val):
            logger.warning("Valor fuera de rango para '%s': %s (esperado [%s, %s])",
                           field, value, min_val, max_val
            )
    return row

def validate_forecast_row(row: dict) -> dict:
    """Valida y limpia un diccionario con los campos de ForecastDay.

    - Lanza RuntimeError si algún campo requerido es None.
    - Loguea advertencia si un valor está fuera de rango.
    
    Returns: el mismo dict.
    """
    for field in REQUIRED_FIELDS_FORECAST:
        if row.get(field) is None:
            raise RuntimeError(
                f"Campo requerido '{field}' es null en el pronóstico de Open-Meteo"
            )

    for field, value in row.items():
        if value is None or field not in RANGES:
            continue
        min_val, max_val = RANGES[field]
        if not (min_val <= value <= max_val):
            logger.warning(
                "Valor fuera de rango para '%s': %s (esperado [%s, %s])",
                field, value, min_val, max_val,
            )

    return row