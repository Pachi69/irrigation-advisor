"""
Estrategias de riego de la simulación final y mediciones de cada temporada.

- Sistema (regla de umbral): cada día de consulta decide con el agotamiento al
  final del día anterior; si alcanza o supera RAW, riega ese mismo día una lámina
  igual al agotamiento. Es lo que hace el sistema cuando no obtiene pronóstico
  (urgency_from_balance). Si el productor consulta el sistema cada cierta
  cantidad de días, el sistema solo decide en los días de consulta.
- Calendario planificado: riega cada 7, 10 o 14 días sin mirar el estado del
  suelo ni el clima de la temporada. Cada lámina es el requerimiento medio de los
  días desde ese riego hasta el día anterior al siguiente.
- Calendario a igual agua: mismas fechas y proporciones que el calendario
  planificado, con las láminas escaladas al agua neta que aplicó el sistema.

Todas las temporadas empiezan con el suelo a capacidad de campo (agotamiento 0).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, fields
from statistics import mean

from .balance import DayResult, Step, closure_residual
from .data import EFFICIENCY

CALENDAR_INTERVALS = [7, 10, 14]

# Decision de riego de un dia:
# (indice del dia, resultados de los dias anteriores en el balance del sistema) -> riego neto (mm)
Decision = Callable[[int, list[DayResult]], float]


def threshold_rule(raw: float, every: int = 1, first: int = 0) -> Decision:
    """Regla de umbral, con consultas cada 'every' dias a partir del dia 'first': riega
    el agotamiento cuando alcanza o supera RAW, redondeado a 0,1 mm como la lamina que
    recomienda el sistema. El primer dia de la temporada el suelo esta a capacidad de
    campo, asi que no riega."""
    def decide(i: int, past: list[DayResult]) -> float:
        if i % every != first or not past:
            return 0.0
        dr = past[-1].dr
        return round(dr, 1) if dr >= raw else 0.0
    return decide

def planned_doses(interval: int, first: int, requirement: list[float]) -> dict[int, float]:
    """Laminas del calendario planificado: riega cada 'interval' dias a partir del dia
    'first'. Cada lamina es el requerimiento de los dias desde ese riego hasta el dia
    anterior al siguiente (el ultimo, hasta el fin de la temporada); requirement tiene
    el requerimiento de cada dia de la temporada."""
    return {d: sum(requirement[d:d + interval]) for d in range(first, len(requirement), interval)}

def scaled_doses(doses: dict[int, float], net_mm: float) -> dict[int, float]:
    """Calendario a igual agua: mismas fechas y proporciones que 'doses', con laminas
    que suman net_mm."""
    planned = sum(doses.values())
    return {d: net_mm * v / planned for d, v in doses.items()}

def calendar(doses: dict[int, float]) -> Decision:
    """Calendario: riega en los dias de 'doses' la lamina indicada, sin mirar el balance."""
    def decide(i: int, past: list[DayResult]) -> float:
        return doses.get(i, 0.0)
    return decide

def simulate(n_days: int, decide: Decision, real: Step, estimated: Step | None = None) -> list[DayResult]:
    """Simula una temporada y devuelve los resultados diarios del balance real.
    Cada dia, 'decide' elige el riego con los resultados de los dias anteriores del
    balance que estima el sistema, y ese riego se aplica en los dos balances. Sin
    balance estimado, el sistema conoce el suelo sin error y decide con el real.
    """
    real_res: list[DayResult] = []
    est_res = real_res if estimated is None else []
    for i in range(n_days):
        irrigation = decide(i, est_res)
        real_res.append(real(i, real_res[-1].dr if real_res else 0.0, irrigation))
        if estimated is not None:
            est_res.append(estimated(i, est_res[-1].dr if est_res else 0.0, irrigation))
    return real_res


@dataclass(frozen=True)
class Metrics:
    """Mediciones de una temporada."""
    net_mm: float # riego neto
    gross_mm: float # riego bruto: neto / eficiencia de aplicacion
    dr_final_mm: float # agotamiento al final de la temporada
    total_mm: float # agua total: riego neto + agotamiento final
    perc_mm: float # percolacion
    pe_mm: float # precipitacion efectiva
    etc_mm: float # ETc total
    eta_mm: float # ETa total
    eta_etc: float # ETa / ETc
    stress_days: float # dias con Ks de inicio menor a 1
    ks_min: float # Ks de inicio minimo
    irrigations: float # cantidad de riegos
    closure_mm: float # control de cierre del balance

def season_metrics(results: list[DayResult]) -> Metrics:
    """Mediciones de una temporada a partir de sus resultados diarios."""
    net = sum(r.irrigation for r in results)
    etc = sum(r.etc for r in results)
    eta = sum(r.eta for r in results)
    return Metrics(
        net_mm=net,
        gross_mm=net / EFFICIENCY,
        dr_final_mm=results[-1].dr,
        total_mm=net + results[-1].dr,
        perc_mm=sum(r.perc for r in results),
        pe_mm=sum(r.pe for r in results),
        etc_mm=etc,
        eta_mm=eta,
        eta_etc=eta / etc,
        stress_days=sum(r.ks_start < 1 for r in results),
        ks_min=min(r.ks_start for r in results),
        irrigations=sum(r.irrigation > 0 for r in results),
        closure_mm=closure_residual(results),
    )


def calendar_runs(interval: int, requirement: list[float], real: Step,
                  net_mm: float | None = None) -> list[Metrics]:
    """Mediciones del calendario con cada una de las fechas de inicio posibles. Sin
    net_mm, el calendario planificado; con net_mm (el riego neto del sistema), el
    calendario a igual agua."""
    runs = []
    for first in range(interval):
        doses = planned_doses(interval, first, requirement)
        if net_mm is not None:
            doses = scaled_doses(doses, net_mm)
        runs.append(season_metrics(simulate(len(requirement), calendar(doses), real)))
    return runs

def query_runs(every: int, raw: float, real: Step, n_days: int) -> list[Metrics]:
    """Mediciones del sistema con consultas cada 'every' dias, con cada uno de los
    dias de inicio posibles."""
    return [season_metrics(simulate(n_days, threshold_rule(raw, every, first), real))
            for first in range(every)]

def summarize(runs: list[Metrics]) -> dict[str, Metrics]:
    """Promedio, minimo y maximo de cada medicion entre las fechas de inicio."""
    names = [f.name for f in fields(Metrics)]
    return {stat: Metrics(**{n: fn(getattr(m, n) for m in runs) for n in names})
            for stat, fn in (("promedio", mean), ("minimo", min), ("maximo", max))}