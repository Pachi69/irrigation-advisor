"""
Balance hídrico diario FAO-56 de la simulación final.

Hay dos versiones del mismo balance diario:
- system_balance: el balance del sistema (calculate_water_balance), sin cambios.
- modified_balance: las mismas ecuaciones, con parámetros que pueden diferir de
  los que usa el sistema: ETo multiplicada por un factor, Kc más un desvío, otro
  suelo u otro método de lluvia efectiva. calculate_water_balance no admite esos
  cambios y el código del sistema no se modifica, por eso las ecuaciones se
  escriben acá. Con los parámetros del sistema da el mismo resultado que
  system_balance (lo verifica test_balance.py).

modified_balance sirve para medir el efecto de errores en los datos de entrada.
Se simulan dos suelos en paralelo que reciben el mismo riego: el sistema decide
con system_balance (lo que cree que pasa en el suelo) y los resultados se miden
con modified_balance (lo que pasa en el suelo cuando los datos del sistema tienen
error).

Las dos devuelven también la ETa del día (Ks de inicio del día × Kc × ETo), que
calculate_water_balance calcula pero no devuelve. Se calcula aparte, sin deducirla
del cambio de agotamiento, para que el control de cierre del balance verifique algo.
"""

from __future__ import annotations
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from app.calculation.water_balance import (
    _SOIL_PROPS,
    _water_stress_coefficient,
    calculate_water_balance,
    effective_precipitation,
)
from app.models.enums import SoilType
from app.schemas.calculation import EToResult, WaterBalanceResult

from .data import P, ROOT_DEPTH, SOIL, Day


class RainMethod(str, Enum):
    system = "system" # el del sistema: 0 si la lluvia es menor a 0.2 * ETo del dia; toda la lluvia si no
    brouwer = "brouwer" # mensual de Brouwer y Heibloem (1986)

@dataclass(frozen=True)
class BalanceParams:
    """Parametros del balance. Por defecto, los del caso de estudio."""
    soil: SoilType = SOIL
    p: float = P
    root_depth: float = ROOT_DEPTH
    eto_factor: float = 1.0
    kc_offset: float = 0.0
    rain: RainMethod = RainMethod.system

    @property
    def taw(self) -> float:
        s = _SOIL_PROPS[self.soil]
        return 1000 * (s["theta_fc"] - s["theta_wp"]) * self.root_depth

    @property
    def raw(self) -> float:
        return self.p * self.taw

@dataclass(frozen=True, slots=True)
class DayResult:
    dr: float # agotamiento al final del día (mm)
    ks_start: float # Ks al inicio del día, con el agotamiento del día anterior
    ks: float # Ks al final del dia
    etc: float # ETc = Kc * ETo (mm)
    eta: float # ETa = Ks de inicio * ETc (mm)
    pe: float # lluvia efectiva (mm)
    irrigation: float # riego neto (mm)
    perc: float # percolación (mm)
    water_balance: WaterBalanceResult | None = None # resultado de calculate_water_balance; None en modified_balance


# un dia del balance: (indice del dia, agotamiento del dia anterior, riego neto) -> resultado
Step = Callable[[int, float, float], DayResult]

def effective_rain(days: list[Day], eto: list[float], method: RainMethod) -> list[float]:
    """Lluvia efectiva de cada dia de la temporada (mm). 'eto' es la ETo de cada dia del
    balance: la regla del sistema la usa para el umbral de 0.2 * ETo."""
    if method is RainMethod.system:
        return [effective_precipitation(x.precip_mm, e) for x, e in zip(days, eto)]

    # Brouwer y Heibloem (1986), seccion 4.2. Con la lluvia del mes P:
    # Pe del mes = 0,6 * P - 10 si P < 75 mm; 0,8 * P - 25 si P >= 75 mm; minimo 0.
    # Se reparte entre los dias del mes en proporcion a la lluvia de cada dia.
    month_rain: dict[tuple[int, int], float] = defaultdict(float)
    for x in days:
        month_rain[(x.date.year, x.date.month)] += x.precip_mm
    pe = []
    for x in days:
        p_month = month_rain[(x.date.year, x.date.month)]
        if p_month == 0:
            pe.append(0.0)
            continue
        pe_month = 0.6 * p_month - 10 if p_month < 75 else 0.8 * p_month - 25
        pe.append(max(0.0, pe_month) * x.precip_mm / p_month)
    return pe

def system_balance(days: list[Day], soil: SoilType = SOIL, p: float = P) -> Step:
    """Balance del sistema (calculate_water_balance) para una temporada."""
    etos = [EToResult(eto_mm=x.eto_mm) for x in days]

    def step(i: int, prev_dr: float, irrigation: float) -> DayResult:
        x = days[i]
        res = calculate_water_balance(etos[i], x.kc, x.precip_mm, prev_dr, soil, ROOT_DEPTH, p, irrigation_mm=irrigation)
        # ETa: misma formula que calculate_water_balance usa internamente
        ks_start = _water_stress_coefficient(prev_dr, res.raw_mm, res.taw_mm)
        etc = x.kc.kc * x.eto_mm
        return DayResult(dr=res.water_deficit_mm, ks_start=ks_start, ks=res.ks, etc=etc,
                    eta=ks_start * etc, pe=effective_precipitation(x.precip_mm, x.eto_mm),
                    irrigation=irrigation, perc=res.deep_percolation_mm,
                    water_balance=res)
    return step

def modified_balance(days: list[Day], params: BalanceParams) -> Step:
    """Balance con parametros modificados para una temporada.
    
    Mismas ecuaciones que calculate_water_balance: Ks con el agotamiento de inicio
    del dia, ETa = Ks * ETc, Dr = Dr anterior - (Pe + riego) + ETa; el exceso sobre
    capacidad de campo es percolacion y Dr queda entre 0 y TAW.
    """
    eto = [params.eto_factor * x.eto_mm for x in days]
    pe = effective_rain(days, eto, params.rain)
    kc = [x.kc.kc + params.kc_offset for x in days]
    taw, raw = params.taw, params.raw

    def step(i: int, prev_dr: float, irrigation: float) -> DayResult:
        etc = kc[i] * eto[i]
        ks_start = _water_stress_coefficient(prev_dr, raw, taw)
        eta = ks_start * etc
        balance = prev_dr - (pe[i] + irrigation) + eta
        dr = max(0.0, min(balance, taw))
        return DayResult(dr=dr, ks_start=ks_start, ks=_water_stress_coefficient(dr, raw, taw),
                         etc=etc, eta=eta, pe=pe[i], irrigation=irrigation,
                         perc=max(0.0, -balance))

    return step

def closure_residual(results: list[DayResult], dr_start: float = 0.0) -> float:
    """Control de cierre de la temporada (mm); debe dar cerca de 0:
    Sumatoria(Pe + riego - ETa - percolacion) + (agotamiento final - agotamiento inicial)."""
    flows = sum(r.pe + r.irrigation - r.eta - r.perc for r in results)
    return flows + (results[-1].dr - dr_start)