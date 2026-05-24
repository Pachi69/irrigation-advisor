"""Cliente Open-Meteo para datos climáticos (actuales, recientes, pronóstico).

Usa la Forecast API con parámetro `past_days` para cubrir hoy y días pasados
(hasta 92 días atrás). Timezone America/Argentina/Mendoza para que los días
se alineen con el calendario local.
"""

import logging
from datetime import date, timedelta
import time

import httpx
import requests

logger = logging.getLogger(__name__)

from app.schemas.climate import ClimateData, ForecastDay
from app.ingestion.validation import validate_climate_row, validate_forecast_row
from app.ingestion import nasa_power

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

def _fetch_daily(params: dict, retries: int = 3, backoff: float = 2.0) -> dict:
    """Helper: Hace GET a Open-Meteo y devuelve la seccion 'daily' del payload"""
    last_err = None
    for attempt in range(retries):
        try:
            response = httpx.get(OPEN_METEO_FORECAST_URL, params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
            daily = payload.get("daily")
            if not daily or not daily.get("time"):
                raise RuntimeError("Open-Meteo devolvio respuesta vacia o sin seccion daily")
            return daily
        except (httpx.HTTPError, RuntimeError) as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
    raise RuntimeError(f'Error al obtener datos climaticos tras {retries} intentos: {last_err}')

def _climate_data_from_daily(daily: dict, idx: int, target_date: date) -> ClimateData:
    """Construye un ClimateData desde la fila `idx` del payload 'daily' de Open-Meteo.

    Args:
        daily:       seccion 'daily' del payload (la que devuelve _fetch_daily).
        idx:         indice de la fila a extraer dentro de las listas de `daily`.
        target_date: fecha que corresponde a esa fila.

    Returns:
        ClimateData validado para esa fecha.
    """
    pressure_hpa = daily["surface_pressure_mean"][idx]
    pressure_kpa = pressure_hpa / 10.0 if pressure_hpa is not None else None

    row = validate_climate_row({
        "temp_max_c":         daily["temperature_2m_max"][idx],
        "temp_min_c":         daily["temperature_2m_min"][idx],
        "temp_mean_c":        daily["temperature_2m_mean"][idx],
        "humidity_pct":       daily["relative_humidity_2m_mean"][idx],
        "wind_speed_10m":     daily["wind_speed_10m_mean"][idx],
        "solar_radiation_mj": daily["shortwave_radiation_sum"][idx],
        "precipitation_mm":   daily["precipitation_sum"][idx],
        "pressure_kpa":       pressure_kpa,
        "eto_reference_mm":   daily["et0_fao_evapotranspiration"][idx],
    })
    return ClimateData(date=target_date, **row)

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

    try:
        daily = _fetch_daily(params)

        # Ubicamos el índice exacto de target_date en la lista devuelta
        dates = daily["time"]
        try:
            idx = dates.index(target_date.isoformat())
        except ValueError as e:
            raise RuntimeError(
                f"Open-Meteo no devolvio datos para la fecha {target_date} (fechas recibidas: {dates})"
            ) from e

        return _climate_data_from_daily(daily, idx, target_date)

    except RuntimeError as open_meteo_error:
        logger.warning(
            "Open-Meteo falló (%s); intentando NASA POWER como respaldo.", open_meteo_error
        )
        try:
            return nasa_power.get_climate_data(latitude, longitude, target_date)
        except RuntimeError as nasa_error:
            raise RuntimeError(
                f"Ambas fuentes fallaron. Open-Meteo: {open_meteo_error}. NASA POWER: {nasa_error}"
            ) from nasa_error
        
def get_climate_data_for_range(
        latitude: float, longitude: float, start_date: date, end_date: date
) -> dict[date, ClimateData]:
    """Obtiene datos climaticos diarios para un rango de fechas.
    
    Reemplaza N llamadas dia-por-dia de get_climate_data por una unica request,
    pensado para el backfill.

    Args:
        latitude:   latitud en grados decimales.
        longitude:  longitud en grados decimales.
        start_date: primer dia del rango (inclusive). No futuro, no > 92 dias.
        end_date:   ultimo dia del rango (inclusive). No futuro.

    Returns:
        dict {fecha: ClimateData}, una entrada por cada dia con datos validos.

    Raises:
        ValueError:   si las fechas son invalidas (futuras, mal ordenadas o
                      start_date supera los 92 dias de past_days).
        RuntimeError: si Open-Meteo falla y NASA POWER tampoco devuelve nada.
    """
    today = date.today()

    if start_date > end_date:
        raise ValueError(f"start_date {start_date} es posterior a end_date {end_date}")
    if end_date > today:
        raise ValueError(f"end_date {end_date} es futura; usar get_forecast para el pronóstico.")
    
    delta_days = (today - start_date).days
    if delta_days > 92:
        raise ValueError(f"start_date {start_date} supera los 92 dias de past_days soportados")
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join(DAILY_VARS_FULL),
        "timezone": TIMEZONE,
        "wind_speed_unit": "ms", # FAO-56 requiere m/s, no km/h
        "past_days": delta_days,
        "forecast_days": 1,
    }

    try:
        daily = _fetch_daily(params)
    except RuntimeError as open_meteo_error:
        logger.warning("Open-Meteo fallo para el rango %s..%s (%s); usando NASA POWER dia por dia.", start_date, end_date, open_meteo_error)
        fallback: dict[date, ClimateData] = {}
        current = start_date
        while current <= end_date:
            try:
                fallback[current] = nasa_power.get_climate_data(latitude, longitude, current)
            except RuntimeError as nasa_error:
                logger.warning("NASA POWER fallo para %s: %s; dia omitido.", current, nasa_error)
            current += timedelta(days=1)
        if not fallback:
            raise RuntimeError(
                f"Ambas fuentes fallaron para el rango {start_date}..{end_date}. "
                f"Open-Meteo: {open_meteo_error}") from open_meteo_error
        
        return fallback
    
    result: dict[date, ClimateData] = {}
    for idx, iso_date in enumerate(daily["time"]):
        current = date.fromisoformat(iso_date)
        if current < start_date or current > end_date:
            continue
        try:
            result[current] = _climate_data_from_daily(daily, idx, current)
        except Exception as e:
            logger.warning("Fila climatica invalida para %s: %s; dia omitido", current, e)
            continue

    return result


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


def get_elevation(lat: float, lon: float) -> float | None:
    """Obtiene la elevacion en metros desde Open-Meteo (SRTM-90)."""
    try:
        url = "https://api.open-meteo.com/v1/elevation"
        resp = requests.get(url, params={"latitude": lat, "longitude": lon}, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        elevation = resp.json().get("elevation", [None])[0]
        if elevation is not None:
            logger.info("Elevacion obtenida: %.1f m para (%.4f, %.4f)", elevation, lat, lon)
        return float(elevation) if elevation is not None else None
    except Exception as e:
        logger.warning("No se pudo obtener elevacion: %s", e)
        return None