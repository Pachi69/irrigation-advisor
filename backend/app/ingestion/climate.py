"""Cliente Open-Meteo para datos climáticos (actuales, recientes, pronóstico).

Usa la Forecast API con parámetro `past_days` para cubrir hoy y días pasados,
y la Archive API (ERA5) para el histórico del backfill, ya que la Forecast API
solo retiene ~3 semanas reales hacia atrás (acepta hasta 92 días de `past_days`
pero los más viejos vuelven null). Timezone America/Argentina/Mendoza para que
los días se alineen con el calendario local.
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
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
ARCHIVE_LAG_DAYS = 15
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

def _fetch_daily(params: dict, url: str = OPEN_METEO_FORECAST_URL, retries: int = 3, backoff: float = 2.0) -> dict:
    """Helper: Hace GET a Open-Meteo y devuelve la seccion 'daily' del payload"""
    last_err = None
    for attempt in range(retries):
        try:
            response = httpx.get(url, params=params, timeout=TIMEOUT_SECONDS)
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

def _archive_params(latitude: float, longitude: float, start: date, end: date) -> dict:
    """Parametros para la Archive API (ERA5): rango explicito por fechas ISO"""
    return {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join(DAILY_VARS_FULL),
        "timezone": TIMEZONE,
        "wind_speed_unit": "ms",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }

def _merge_daily_into(
    result: dict[date, ClimateData], daily: dict, start: date, end: date
) -> None:
    """Vuelca las filas de un payload 'daily' al dict result, filtrando por rango."""
    for idx, iso_date in enumerate(daily["time"]):
        current = date.fromisoformat(iso_date)
        if current < start or current > end:
            continue
        try:
            result[current] = _climate_data_from_daily(daily, idx, current)
        except Exception as e:
            logger.warning("Fila climatica invalida para %s: %s; dia omitido", current, e)
            continue


def _fill_from_nasa(
    result: dict[date, ClimateData],
    latitude: float, longitude: float,
    start: date, end: date,
) -> None:
    """Rellena un tramo dia por dia desde NASA POWER (fallback)."""
    current = start
    while current <= end:
        if current not in result:
            try:
                result[current] = nasa_power.get_climate_data(latitude, longitude, current)
            except RuntimeError as nasa_error:
                logger.warning("NASA POWER fallo para %s: %s; dia omitido.", current, nasa_error)
        current += timedelta(days=1)

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
        
def get_climate_data_for_range( latitude: float, longitude: float, start_date: date, end_date: date) -> dict[date, ClimateData]:
    """Obtiene datos climaticos diarios para un rango de fechas.

    Reemplaza N llamadas dia-por-dia de get_climate_data por una (o dos)
    requests batch, pensado para el backfill. Hace un split por antiguedad
    porque el Forecast API solo retiene ~3 semanas de datos reales hacia atras
    (pide hasta 92 dias de past_days pero los devuelve null):
      - Fechas <= hoy - ARCHIVE_LAG_DAYS: Archive API (ERA5), que SI trae el
        historico completo (incluido et0) para fechas viejas.
      - Fechas mas recientes: Forecast API via past_days.
    Ambos tramos se mergean.

    Args:
        latitude:   latitud en grados decimales.
        longitude:  longitud en grados decimales.
        start_date: primer dia del rango (inclusive). No futuro.
        end_date:   ultimo dia del rango (inclusive). No futuro.

    Returns:
        dict {fecha: ClimateData}, una entrada por cada dia con datos validos.

    Raises:
        ValueError:   si las fechas son invalidas (futuras o mal ordenadas).
        RuntimeError: si ambas fuentes fallan y no se obtiene ningun dato.
    """
    today = date.today()

    if start_date > end_date:
        raise ValueError(f"start_date {start_date} es posterior a end_date {end_date}")
    if end_date > today:
        raise ValueError(f"end_date {end_date} es futura; usar get_forecast para el pronóstico.")
    
    archive_cutoff = today - timedelta(days=ARCHIVE_LAG_DAYS)

    result: dict[date, ClimateData] = {}
    errors: list[str] = []

    # --- Tramo historico: Archive API (ERA5) ---
    archive_end = min(end_date, archive_cutoff)
    if start_date <= archive_end:
        try:
            daily = _fetch_daily(_archive_params(latitude, longitude, start_date, archive_end),
                                 url=OPEN_METEO_ARCHIVE_URL)
            _merge_daily_into(result, daily, start_date, archive_end)
        except RuntimeError as archive_error:
            logger.warning(
                "Archive API fallo para %s..%s (%s); usando NASA POWER dia por dia.",
                start_date, archive_end, archive_error,
            )
            errors.append(f"Archive: {archive_error}")
            _fill_from_nasa(result, latitude, longitude, start_date, archive_end)

    # --- Tramo reciente: Forecast API (past_days) ---
    forecast_start = max(start_date, archive_cutoff + timedelta(days=1))
    if forecast_start <= end_date:
        delta_days = (today - forecast_start).days
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ",".join(DAILY_VARS_FULL),
            "timezone": TIMEZONE,
            "wind_speed_unit": "ms",  # FAO-56 requiere m/s, no km/h
            "past_days": delta_days,
            "forecast_days": 1,
        }
        try:
            daily = _fetch_daily(params)
            _merge_daily_into(result, daily, forecast_start, end_date)
        except RuntimeError as forecast_error:
            logger.warning(
                "Forecast API fallo para %s..%s (%s); usando NASA POWER dia por dia.",
                forecast_start, end_date, forecast_error,
            )
            errors.append(f"Forecast: {forecast_error}")
            _fill_from_nasa(result, latitude, longitude, forecast_start, end_date)

    if not result:
        raise RuntimeError(
            f"Ambas fuentes fallaron para el rango {start_date}..{end_date}. "
            + " | ".join(errors)
        )

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