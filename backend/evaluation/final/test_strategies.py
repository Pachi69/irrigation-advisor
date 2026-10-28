"""
Prueba de las estrategias de la simulación final, en las tres temporadas del caso
de estudio y las nueve combinaciones de suelo y fracción de agotamiento p:
- el calendario planificado aplica el requerimiento medio de los días que cubre
  (desde su primer riego hasta el fin de la temporada), con cada intervalo y cada
  fecha de inicio;
- el calendario a igual agua aplica exactamente el riego neto del sistema;
- en cada corrida, el agua total es igual a ETa + percolación − precipitación
  efectiva. Corridas: sistema, calendario planificado y calendario a igual agua;
  y el sistema con consultas cada 1, 3, 5 y 7 días, con cada día de inicio, en la
  configuración del caso de estudio.
Diferencia absoluta menor a 1e-9 en todos los casos.

Uso (desde backend/):  venv/Scripts/python.exe -m evaluation.final.test_strategies
"""
from __future__ import annotations

from app.models.enums import SoilType

from .balance import BalanceParams, system_balance
from .data import daily_requirement, load_climate_series, load_seasons, planned_requirement
from .strategies import (CALENDAR_INTERVALS, Metrics, calendar_runs, query_runs,
                         season_metrics, simulate, threshold_rule)

TOL = 1e-9
SOILS = [SoilType.loamy_sand, SoilType.sandy_loam, SoilType.loam]
PS = [0.40, 0.45, 0.50]
QUERY_EVERY = [1, 3, 5, 7] # dias entre consultas del productor

def main() -> None:
    max_diff = dict.fromkeys(["calendario planificado", "calendario a igual agua", "agua total"], 0.0)

    def check(test: str, case: str, got: float, expected: float) -> None:
        d = abs(got - expected)
        assert d < TOL, f"{case}: {test} difiere en {d}"
        max_diff[test] = max(max_diff[test], d)

    def check_total(case: str, m: Metrics) -> None:
        check("agua total", case, m.total_mm, m.eta_mm + m.perc_mm - m.pe_mm)

    seasons = load_seasons()
    climate = load_climate_series()
    runs = 0
    for label, days in seasons.items():
        months = planned_requirement(label, seasons, climate)
        requirement = daily_requirement(days, months)
        season_total = sum(r.requirement_mm for r in months)
        for soil in SOILS:
            for p in PS:
                case = f"{label}, {soil.value}, p={p}"
                real = system_balance(days, soil, p)
                system = season_metrics(simulate(len(days), threshold_rule(BalanceParams(soil=soil, p=p).raw), real))
                check_total(case, system)
                runs += 1
                for interval in CALENDAR_INTERVALS:
                    planned = calendar_runs(interval, requirement, real)
                    same_water = calendar_runs(interval, requirement, real, system.net_mm)
                    for first, (m_plan, m_same) in enumerate(zip(planned, same_water)):
                        c = f"{case}, cada {interval} dias desde el dia {first}"
                        # los dias anteriores al primer riego no los cubre el calendario
                        check("calendario planificado", c, m_plan.net_mm, season_total - sum(requirement[:first]))
                        check("calendario a igual agua", c, m_same.net_mm, system.net_mm)
                        check_total(c, m_plan)
                        check_total(c, m_same)
                        runs += 2
        real = system_balance(days)
        for every in QUERY_EVERY:
            for first, m in enumerate(query_runs(every, BalanceParams().raw, real, len(days))):
                check_total(f"{label}, consulta cada {every} dias desde el dia {first}", m)
                runs += 1
    print(f"Corridas comparadas: {runs}")
    print("Mayor diferencia absoluta:")
    for test, d in max_diff.items():
        print(f" {test}: {d:.1e}")
    print(f"OK: todas menores a {TOL:.0e}")

if __name__ == "__main__":
    main()