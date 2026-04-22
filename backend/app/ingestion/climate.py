"""Cliente Open-Meteo para datos climáticos (actuales, recientes, pronóstico).

Usa la Forecast API con parámetro `past_days` para cubrir hoy y días pasados
(hasta 92 días atrás). Timezone America/Argentina/Mendoza para que los días
se alineen con el calendario local.
"""

from datetime import date

import httpx

from app.schemas.climate import ClimateData, ForecastDay
from app.ingestion.validation import validate_climate_row, validate_forecast_row

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEZONE = "America/Argentina/Mendoza"
TIMEOUT_SECONDS = 10.0

# Variables diarias requeridas para construir ClimateData
DAILY_VARS_FULL = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "wind_speed_10m_mean",
    "shortwave_radiation_sum",
    "precipitation_sum",
    "surface_pressure_mean",
    "et0_fao_evapotranspiration",
]

#Variables diarias requeridas para ForecastDay
DAILY_VARS_FORECAST = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_mean",
    "et0_fao_evapotranspiration",
]

def _fetch_daily(params: dict) -> dict:
    """Helper: Hace GET a Open-Meteo y devuelve la seccion 'daily' del payload"""
    try:
        response = httpx.get(OPEN_METEO_FORECAST_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"Error al obtener datos climáticos: {e}") from e
    
    daily = payload.get("daily")
    if not daily or not daily.get("time"):
        raise RuntimeError("Open-Meteo devolvio respuesta vacia o sin seccion daily")
    return daily

def get_climate_data(latitude: float, longitude: float, target_date: date) -> ClimateData:
    """Obtiene los datos climaticos diarios para una fecha pasada o actual.
    Args: 
        latitude: latitud del punto en grados decimales
        longitude: longitud del punto en grados decimales
        target_date: fecha a consultar. No puede ser futura.

    Raises:
        ValueError: si target_date es futura o demasiado antigua (> 92 dias).
        RuntimeError: si Open-Meteo falla o no devuelve datos para la fecha.
    """
    today = date.today()
    delta_days = (today - target_date).days

    if delta_days < 0:
        raise ValueError(
            f"target_date {target_date} es futura; usar get_forecast para el pronóstico."
        )
    if delta_days > 92:
        raise ValueError(
            f"target_date {target_date} supera los 92 dias de past_days soportados"
        )
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join(DAILY_VARS_FULL),
        "timezone": TIMEZONE,
        "wind_speed_unit": "ms", # FAO-56 requiere m/s, no km/h
        "past_days": delta_days,
        "forecast_days": 1,
    }

    daily = _fetch_daily(params)

    # Ubicamos el índice exacto de target_date en la lista devuelta
    dates = daily["time"]
    try:
        idx = dates.index(target_date.isoformat())
    except ValueError as e:
        raise RuntimeError(
            f"Open-Meteo no devolvio datos para la fecha {target_date} (fechas recibidas: {dates})"
        ) from e

    pressure_hpa = daily["surface_pressure_mean"][idx]
    pressure_kpa = pressure_hpa / 10.0 if pressure_hpa is not None else None

    row = validate_climate_row({
        "temp_max_c":        daily["temperature_2m_max"][idx],
        "temp_min_c":        daily["temperature_2m_min"][idx],
        "temp_mean_c":       daily["temperature_2m_mean"][idx],
        "humidity_pct":      daily["relative_humidity_2m_mean"][idx],
        "wind_speed_10m":    daily["wind_speed_10m_mean"][idx],
        "solar_radiation_mj": daily["shortwave_radiation_sum"][idx],
        "precipitation_mm":  daily["precipitation_sum"][idx],
        "pressure_kpa":      pressure_kpa,
        "eto_reference_mm":  daily["et0_fao_evapotranspiration"][idx],
    })

    return ClimateData(date=target_date, **row)

def get_forecast(latitude: float, longitude: float, days: int = 5) -> list[ForecastDay]:
    """Obtiene el pronóstico de los próximos N días (incluyendo hoy).

    Args:
        latitude: latitud en grados decimales.
        longitude: longitud en grados decimales.
        days: cantidad de días a pronosticar. Rango válido [1, 16].

    Raises:
        ValueError: si days está fuera de rango.
        RuntimeError: si Open-Meteo falla.
    """
    if not 1 <= days <= 16:
        raise ValueError(f"days={days} fuera de rango [1, 16]")
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join(DAILY_VARS_FORECAST),
        "timezone": TIMEZONE,
        "forecast_days": days,
    }

    daily = _fetch_daily(params)

    result = []
    for i, iso_date in enumerate(daily["time"]):
        row = validate_forecast_row({
            "temp_max_c":                    daily["temperature_2m_max"][i],
            "temp_min_c":                    daily["temperature_2m_min"][i],
            "precipitation_mm":              daily["precipitation_sum"][i],
            "precipitation_probability_pct": daily["precipitation_probability_mean"][i],
            "eto_reference_mm":              daily["et0_fao_evapotranspiration"][i],
        })
        result.append(ForecastDay(date=date.fromisoformat(iso_date), **row))

    return result