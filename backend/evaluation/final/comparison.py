"""
Comparación del sistema con el calendario planificado y criterio de éxito de la
simulación final.

Para cada caso (temporada y configuración, escenario de error o frecuencia de
consulta) y cada intervalo del calendario se usa el promedio de las fechas de
inicio del calendario.

Criterio de éxito de un caso: es favorable si se cumplen las tres condiciones:
1. la ETa/ETc del sistema es igual o mayor a 0,70 (se informa también si alcanza 0,80);
2. el agua total del sistema es menor que la del calendario planificado en cada
   uno de los tres intervalos;
3. la percolación del sistema es igual o menor que la menor de los tres
   intervalos del calendario planificado.
"""
from __future__ import annotations

from dataclasses import dataclass

from .strategies import Metrics

ETA_ETC_MIN = 0.70 # vid para vinificacion (Keller et al., 2016; Intrigliolo et al., 2012)
ETA_ETC_TABLE_GRAPE = 0.80 # uva de mesa (Permanhani et al., 2016; El-Salhy et al., 2026); solo se informa

def eta_etc(m: Metrics) -> float:
    """ETa/ETc redondeada a 3 decimales, como se usa en las comparaciones."""
    return round(m.eta_etc, 3)

@dataclass(frozen=True)
class WaterDifference:
    """Diferencia de agua entre el sistema y un calendario (sistema - calendario).
    Por el cierre del balance, y porque la precipitacion efectiva es la misma en las
    dos estrategias, total_mm = perc_mm + eta_mm."""
    total_mm: float # diferencia de agua total
    total_pct: float # en % del agua total del calendario
    perc_mm: float # diferencia de percolacion
    eta_mm: float # diferencia de ETa

def water_difference(system: Metrics, calendar: Metrics) -> WaterDifference:
    if abs(system.pe_mm - calendar.pe_mm) > 1e-9:
        raise ValueError("El sistema y el calendario deben evaluarse con la misma precipitacion efectiva.")
    diff = system.total_mm - calendar.total_mm
    return WaterDifference(
        total_mm=diff,
        total_pct=100 * diff / calendar.total_mm,
        perc_mm=system.perc_mm - calendar.perc_mm,
        eta_mm=system.eta_mm - calendar.eta_mm,
    )

@dataclass(frozen=True)
class Criterion:
    """Resultado del criterio de exito en un caso."""
    crop: bool # 1: ETa/ETc del sistema >= ETA_ETC_MIN
    crop_table_grape: bool # se informa: ETa/ETc del sistema >= ETA_ETC_TABLE_GRAPE
    water: bool # 2: agua total del sistema menor que la del calendario en cada intervalo
    percolation: bool # 3: percolacion del sistema <= la menor de los intervalos del calendario

    @property
    def favorable(self) -> bool:
        return self.crop and self.water and self.percolation

def criterion(system: Metrics, planned: dict[int, Metrics]) -> Criterion:
    """Criterio de exito de un caso. planned: promedio de las fechas de inicio del
    calendario planificado en cada intervalo."""
    return Criterion(
        crop=eta_etc(system) >= ETA_ETC_MIN,
        crop_table_grape=eta_etc(system) >= ETA_ETC_TABLE_GRAPE,
        water=all(system.total_mm < m.total_mm for m in planned.values()),
        percolation=system.perc_mm <= min(m.perc_mm for m in planned.values()),
    )