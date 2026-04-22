"""Cliente NASA POWER como fuente de respaldo para datos climaticos historicos.

Solo soporta datos pasados (no pronostico). Se usa cuando Open-Meteo no esta disponible.
Resolucion espacial : ~55 km (inferior a Open-Meteo/ERA5 a 9km).
"""

from datetime import date

import httpx

from app.schemas.climate import ClimateData
from app.ingestion.validation import validate_climate_row

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
TIMEOUT_SECONDS = 15.0
NASA_FILL_VALUE = -999.0 

# Parametros NASA POWER y su nombre interno equivalente
PARAM_MAP = {
    "T2M_MAX":           "temp_max_c",
    "T2M_MIN":           "temp_min_c",
    "T2M":               "temp_mean_c",
    "RH2M":              "humidity_pct",
    "WS10M":             "wind_speed_10m",
    "ALLSKY_SFC_SW_DWN": "solar_radiation_mj",
    "PRECTOTCORR":       "precipitation_mm",
    "PS":                "pressure_kpa",
}

def get_climate_data(latitude: float, longitude: float, target_date: date) -> ClimateData:
    """Obtiene datos climaticos diarios desde NASA POWER para una fecha pasada.
    
    Args:
        latitude: latitud en grados decimales.
        longitude: longitud en grados decimales.
        target_date: fecha a consultar. No puede ser futura.

    Raises:
        ValueError: si target_date es futura.
        RuntimeError: si NASA POWER falla o no devuelve datos para la fecha.
    """
    if target_date > date.today():
        raise ValueError(f"target_date {target_date} es futura; NASA POWER no tiene pronostico.")
    
    date_str = target_date.strftime("%Y%m%d")
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start": date_str,
        "end": date_str,
        "parameters": ",".join(PARAM_MAP.keys()),
        "community": "AG",
        "format": "JSON",
    }

    try:
        response = httpx.get(NASA_POWER_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"Error al obtener datos de NASA POWER: {e}") from e
    
    try:
        parameters = payload["properties"]["parameter"]
    except KeyError as e:
        raise RuntimeError(f"Respuesta inesperada de NASA POWER: falta clave {e}") from e
    
    # Extraemos el valor de cada parametro para la fecha pedida y mapeamos al nombre interno
    row: dict = {"eto_reference_mm": None} # NASA POWER no calcula ETo
    for nasa_key, internal_key in PARAM_MAP.items():
        raw = parameters.get(nasa_key, {}).get(date_str)
        # -999 es el fill value de NASA POWER (dato no disponible)
        row[internal_key] = None if (raw is None or raw == NASA_FILL_VALUE) else raw

    validate_climate_row(row)
    return ClimateData(date=target_date, **row)