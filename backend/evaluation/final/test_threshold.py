"""
Prueba: la regla de umbral da los mismos riegos que urgency_from_balance del sistema
(mismos días y misma lámina), en las tres temporadas del caso de estudio.

Simula cada temporada con la regla de umbral y, cada día, compara su riego con la
lámina que recomienda urgency_from_balance con el balance y el Kc del día anterior.
El primer día no tiene balance del día anterior y la regla no riega.

Uso (desde backend/):  venv/Scripts/python.exe -m evaluation.final.test_threshold
"""
from __future__ import annotations

from app.calculation.urgency import urgency_from_balance

from .balance import BalanceParams, system_balance
from .data import load_seasons
from .strategies import simulate, threshold_rule


def main() -> None:
    raw = BalanceParams().raw
    n = irrigations = 0
    for label, days in load_seasons().items():
        results = simulate(len(days), threshold_rule(raw), system_balance(days))
        for i in range(1, len(days)):
            balance = results[i - 1].water_balance
            assert balance is not None
            expected = urgency_from_balance(balance, days[i - 1].kc).recommended_irrigation_mm
            got = results[i].irrigation
            assert got == expected, f"{label}, {days[i].date}: regla {got} mm, sistema {expected} mm"
            n += 1
            irrigations += got > 0
    print(f"Dias comparados: {n}; con riego: {irrigations}")
    print("OK: mismos dias de riego y misma lamina")

if __name__ == "__main__":
    main()