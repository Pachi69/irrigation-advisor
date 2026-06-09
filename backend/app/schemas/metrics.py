from datetime import date

from pydantic import BaseModel


class WeeklyWaterMetrics(BaseModel):
    """Agua e indicadores agregados por semana ISO (lunes a domingo)"""
    week_start: date    # lunes
    week_end: date      # domingo
    days: int       # días con balance en la semana
    eto_mm: float
    etc_mm: float       # demanda del cultivo (neta)
    effective_rain_mm: float
    net_requirement_mm: float       # IRn = max(0, ETc - lluvia efectiva), neto
    net_requirement_m3: float | None
    applied_mm: float       # neto (confirmaciones de esa semana)
    applied_m3: float | None
    baseline_etc_mm: float      # Reposicion diaria ciega de ETc (neta) = etc_mm
    avoided_mm: float       # baseline_etc_mm - recommended_mm
    avoided_m3: float | None
    avg_ks: float | None
    stress_days: int    # Ks < 1

class WaterSummary(BaseModel):
    net_requirement_mm: float   # IRn = max(0, ETc - lluvia efectiva), neto
    net_requirement_m3: float | None
    applied_mm: float
    applied_m3: float | None
    baseline_etc_mm: float
    baseline_etc_m3: float | None
    avoided_mm: float
    avoided_m3: float | None
    avoided_pct: float | None       # avoided / baseline

class StressSummary(BaseModel):
    days_evaluated: int
    stress_days: int        # Ks < 1
    stress_days_pct: float
    severe_stress_days: int      # Ks < 0.5
    severe_stress_days_pct: float
    avg_ks: float | None
    min_ks: float | None
    avg_deficit_mm: float | None
    avg_deficit_pct: float | None   # deficit / TAW promedio
    max_deficit_mm: float | None
    days_above_raw: int    # deficit > RAW (inicio de estres)

class AdherenceSummary(BaseModel):
    actionable: int     # recomendaciones con mm > 0 en la ventana
    confirmed: int      # de esas cuantas se confirmaron
    pending: int
    adherence_pct: float | None     # confirmed / actionable

class UrgencyDistribution(BaseModel):
    low: int
    medium: int
    high: int
    critical: int

class SatelliteQuality(BaseModel):
    days_evaluated: int
    s2_dynamic_days: int    # Kc satelital
    tabular_days: int       # Kc tabular (fallback)
    s2_dynamic_pct: float
    ndvi_days: int
    avg_ndvi: float | None

class ClimateSummary(BaseModel):
    eto_mm: float
    etc_mm: float
    rain_mm: float
    effective_rain_mm: float

class SectorMetricsResponse(BaseModel):
    sector_id: int
    start_date: date
    end_date: date
    water: WaterSummary
    stress: StressSummary
    adherence: AdherenceSummary
    urgency: UrgencyDistribution
    satellite: SatelliteQuality
    climate: ClimateSummary
    weekly: list[WeeklyWaterMetrics]
