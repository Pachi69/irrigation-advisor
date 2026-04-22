
"""
Cálculo de evapotranspiración de referencia (ETo) por FAO-56 Penman-Monteith.
"""

from __future__ import annotations

import math
from datetime import date

from app.schemas.climate import ClimateData
from app.schemas.calculation import EToResult

# Constante de Stefan-Boltzmann (MJ m⁻² día⁻¹ K⁻⁴)  [Ec. 39]
SIGMA = 4.903e-9

# Albedo superficie de referencia (césped corto)  [Ec. 38]
ALPHA = 0.23

# Constante solar (MJ m⁻² min⁻¹)  [Ec. 21]
GSC = 0.0820


def _elevation_from_pressure(pressure_kpa: float) -> float:
    """Estima la altitud (m s.n.m) a partir de la presion atmosferica (kPa)."""
    return (293.0 - 293.0 * (pressure_kpa / 101.3) ** (1 / 5.26)) / 0.0065

def _saturation_vapor_pressure(temp_c: float) -> float:
    """Presion de vapor de saturacion e°(T) en kPa."""
    return 0.6108 * math.exp(17.27 * temp_c / (temp_c + 273.3))

def _slope_vapor_pressure_curve(temp_c: float) -> float:
    """Pendiente de la curva de presion de vapor (kPa/°C)."""
    return 4098 * _saturation_vapor_pressure(temp_c) / (temp_c + 237.3) ** 2

def _psychrometric_constant(pressure_kpa: float) -> float:
    """Constante psicrometrica y (kPA/°C)."""
    return 0.000665 * pressure_kpa

def _wind_speed_2m(u10: float) -> float:
    """Convierte velocidad del viento de 10m a 2m (m/s)."""
    return u10 * 4.87 / math.log(67.8 * 10 - 5.42)

def _extraterrestrial_radiation(latitude_rad: float, j: int) -> float:
    """Radiacion extraterrestre Ra (MJ m⁻² día⁻¹)"""
    dr = 1 + 0.033 * math.cos(2 * math.pi * j / 365)
    delta = 0.409 * math.sin(2 * math.pi * j / 365)
    omega_s = math.acos(-math.tan(latitude_rad) * math.tan(delta))
    return (
        (24 * 60 / math.pi)
        * GSC
        * dr
        * (
            omega_s * math.sin(latitude_rad) * math.sin(delta)
            + math.cos(latitude_rad) * math.cos(delta) * math.sin(omega_s)
        )
    )

def calculate_eto(
    climate: ClimateData,
    latitude_deg: float,
    target_date: date,
    elevation_m: float | None = None,
) -> EToResult:
    """
    Calcula ETo (mm/dia) por FAO-56 Penman-Monteith.

    Args:
        climate:       Datos climáticos diarios del campo.
        latitude_deg:  Latitud en grados decimales (negativo = hemisferio sur).
        target_date:   Fecha del cálculo (determina el día del año).
        elevation_m:   Altitud (m s.n.m.). Si es None se estima desde la presión.

    Returns:
        EToResult con eto_mm >= 0.

    Raises:
        ValueError: si faltan variables climáticas obligatorias.
    """
    # Datos de entrada
    t_max = climate.temp_max_c
    t_min = climate.temp_min_c
    t_mean = climate.temp_mean_c
    rh = climate.humidity_pct #%
    u10 = climate.wind_speed_10m #m/s a 10 m
    rs = climate.solar_radiation_mj
    p_kpa = climate.pressure_kpa if climate.pressure_kpa is not None else 101.3

    # Verificar variables obligatorias
    required = {
        "temp_max_c": t_max, "temp_min_c": t_min, "temp_mean_c": t_mean,
        "humidity_pct": rh, "wind_speed_10m": u10, "solar_radiation_mj": rs,
    }
    missing = [k for k, v in required.items() if v is None]
    if missing:
        raise ValueError(f"Faltan variables climaticas para ETo: {missing}")
    
    # Altitud
    if elevation_m is None:
        elevation_m = _elevation_from_pressure(p_kpa)

    # Dia del año y latitud en radianes
    j = target_date.timetuple().tm_yday
    phi = math.radians(latitude_deg)

    # Presiones de vapor
    es = (_saturation_vapor_pressure(t_max) + _saturation_vapor_pressure(t_min)) / 2
    ea = rh / 100 * es

    # Delta y gamma
    delta = _slope_vapor_pressure_curve(t_mean)
    gamma = _psychrometric_constant(p_kpa)

    # Viento a 2m
    u2 = _wind_speed_2m(u10)

    # Radiacion neta
    ra = _extraterrestrial_radiation(phi, j)
    rso = max((0.75 + 2e-5 * elevation_m) * ra, 0.01)
    rns = (1 - ALPHA) * rs

    t_max_k = t_max + 273.16
    t_min_k = t_min + 273.16
    rs_rso = min(rs / rso, 1.0)

    rnl = (
        SIGMA
        * (t_max_k**4 + t_min_k**4) / 2
        * (0.34 - 0.14 * math.sqrt(max(ea, 0.001)))
        * (1.35 * rs_rso - 0.35)
    )

    rn = rns - rnl
    g = 0.0 # flujo de calor del suelo ≈ 0 en paso diario

    # FAO-56 Penman-Monteith [Ec. 6]
    numerator = 0.408 * delta * (rn - g) + gamma * (900 / (t_mean + 273)) * u2 * (es - ea)
    denominator = delta + gamma * (1 + 0.34 * u2)

    return EToResult(eto_mm=max(numerator / denominator, 0.0))