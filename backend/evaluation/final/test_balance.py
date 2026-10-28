"""
Prueba: con los parámetros del sistema, modified_balance da el mismo resultado que
el balance del sistema (calculate_water_balance), en cada variable y cada día
(diferencia absoluta menor a 1e-9).

Recorre las tres temporadas, las nueve combinaciones de suelo y fracción de
agotamiento p, y cuatro secuencias de riego que pasan por todos los casos del
balance: sin riego (llega al estrés), riego al llegar a RAW, 60 mm cada 10 días
(percolación) y riegos al azar.

Uso (desde backend/):  venv/Scripts/python.exe -m evaluation.final.test_balance
"""
from __future__ import annotations

import random

from app.calculation.water_balance import calculate_water_balance
from app.models.enums import SoilType
from app.schemas.calculation import EToResult

from .balance import BalanceParams, modified_balance
from .data import ROOT_DEPTH, load_seasons

TOL = 1e-9
SOILS = [SoilType.loamy_sand, SoilType.sandy_loam, SoilType.loam]
PS = [0.40, 0.45, 0.50]

def irrigation_rules(seed: int) -> dict:
    """Secuencias de riego: (dia, agotamiento del dia anterior, RAW) -> riego neto (mm)."""
    rng = random.Random(seed)
    return {
        "sin riego": lambda i, dr, raw: 0.0,
        "riego al llegar a RAW": lambda i, dr, raw: dr if dr >= raw else 0.0,
        "60 mm cada 10 dias": lambda i, dr, raw: 60.0 if i % 10 == 0 else 0.0,
        "al azar": lambda i, dr, raw: rng.uniform(0, 40) if rng.random() < 0.2 else 0.0,
    }

def main() -> None:
    max_diff = dict.fromkeys(["Dr", "Ks", "TAW", "RAW", "percolacion"], 0.0)
    n = stress = perc = rain = 0
    for label, days in load_seasons().items():
        for soil in SOILS:
            for p in PS:
                params = BalanceParams(soil=soil, p=p)
                step = modified_balance(days, params)
                for name, rule in irrigation_rules(seed=0).items():
                    dr_sys = dr_mod = 0.0
                    for i, x in enumerate(days):
                        irr = rule(i, dr_sys, params.raw)
                        res = calculate_water_balance(EToResult(eto_mm=x.eto_mm), x.kc,
                                                    x.precip_mm, dr_sys, soil, ROOT_DEPTH,
                                                    p, irrigation_mm=irr)
                        r = step(i, dr_mod, irr)
                        diffs = {
                            "Dr": abs(res.water_deficit_mm - r.dr),
                            "Ks": abs(res.ks - r.ks),
                            "TAW": abs(res.taw_mm - params.taw),
                            "RAW": abs(res.raw_mm - params.raw),
                            "percolacion": abs(res.deep_percolation_mm - r.perc),
                        }
                        for var, d in diffs.items():
                            assert d < TOL, (f"{label}, {soil.value}, p={p}, {name}, {x.date}: "
                                             f"{var} difiere en {d}")
                            max_diff[var] = max(max_diff[var], d)
                        dr_sys, dr_mod = res.water_deficit_mm, r.dr
                        n += 1
                        stress += r.ks_start < 1
                        perc += r.perc > 0
                        rain += r.pe > 0
    print(f"Dias comparados: {n}")
    print(f" con Ks de inicio menor a 1: {stress}; con percolacion: {perc}; con lluvia efectiva: {rain}")
    print("Mayor diferencia absoluta:")
    for var, d in max_diff.items():
        print(f" {var}: {d:.1e}")
    print(f"OK: todas menores a {TOL:.0e}")

if __name__ == "__main__": 
    main()