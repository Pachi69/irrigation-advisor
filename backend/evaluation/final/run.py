"""
Simulación final de eficiencia hídrica (protocolo de evaluación, versión 2.1).

A partir de los datos guardados en evaluation/_cache/ corre:
- el análisis de sensibilidad: las tres temporadas en las nueve combinaciones de
  suelo y fracción de agotamiento p, que incluyen la del caso de estudio (27 casos);
- el experimento de gemelos: nueve escenarios de error de los datos de entrada, en
  la configuración del caso de estudio;
- la frecuencia de consulta del productor: cada 1, 3, 5 y 7 días, en la
  configuración del caso de estudio.
En cada caso compara el sistema con el calendario planificado y con el calendario
a igual agua y evalúa el criterio de éxito. También escribe el requerimiento medio
y el de cada temporada, y la verificación de los datos climáticos. Los resultados
van a evaluation/final/_out/.

Calendario a igual agua en la frecuencia de consulta: con consultas cada 3, 5 o 7
días, el sistema tiene una corrida por cada día de inicio y cada una aplica distinta
agua neta. Como el caso se evalúa con el promedio de los días de inicio, el
calendario a igual agua de cada frecuencia se escala al agua neta media de esas
corridas. Con consulta diaria hay una sola corrida, así que ese calendario tiene que
coincidir con el del caso de estudio; si no coincide, hay un error en el escalado
(lo verifica check_daily_query).

Uso (desde backend/):  venv/Scripts/python.exe -m evaluation.final.run
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from app.models.enums import SoilType

from .balance import BalanceParams, RainMethod, Step, modified_balance, system_balance
from .climate_check import characterize, verify_eto
from .comparison import ETA_ETC_MIN, criterion, eta_etc, water_difference
from .data import (P, SECTOR_FILE, SOIL, Day, MonthRequirement, daily_requirement, daily_sum_requirement,
                   load_climate_series, load_seasons, planned_requirement, season_requirement)
from .strategies import (CALENDAR_INTERVALS, Metrics, calendar_runs, query_runs, season_metrics,
                         simulate, summarize, threshold_rule)

OUT_DIR = Path(__file__).resolve().parent / "_out"

SOILS = [SoilType.loamy_sand, SoilType.sandy_loam, SoilType.loam]
PS = [0.40, 0.45, 0.50]
QUERY_EVERY = [1, 3, 5, 7] # dias entre consultas del productor

# Escenarios de error (seccion 9 del protocolo): parametros del balance real. El sistema
# decide con el balance de los parametros del caso de estudio.
SCENARIOS = {
    "ETo mayor": BalanceParams(eto_factor=1.15),
    "ETo menor": BalanceParams(eto_factor=0.85),
    "Kc mayor": BalanceParams(kc_offset=0.1),
    "Kc menor": BalanceParams(kc_offset=-0.1),
    "suelo mas liviano": BalanceParams(soil=SoilType.loamy_sand),
    "suelo mas pesado": BalanceParams(soil=SoilType.loam),
    "menos lluvia efectiva": BalanceParams(rain=RainMethod.brouwer),
    "combinado: menos agua de la estimada": BalanceParams(
        eto_factor=1.15, kc_offset=0.1, soil=SoilType.loamy_sand, rain=RainMethod.brouwer),
    "combinado: mas agua de la estimada": BalanceParams(
        eto_factor=0.85, kc_offset=-0.1, soil=SoilType.loam),
}

SENSITIVITY = "sensibilidad"
TWINS = "gemelos"
FREQUENCY = "frecuencia de consulta"
NO_ERROR = "sin error"

SYSTEM = "sistema"
PLANNED = "calendario planificado"
SAME_WATER = "calendario a igual agua"

# Nombres de las columnas de los CSV
METRIC_COLUMNS = {
    "net_mm": "riego_neto_mm",
    "gross_mm": "riego_bruto_mm",
    "dr_final_mm": "agotamiento_final_mm",
    "total_mm": "agua_total_mm",
    "perc_mm": "percolacion_mm",
    "pe_mm": "precipitacion_efectiva_mm",
    "etc_mm": "etc_mm",
    "eta_mm": "eta_mm",
    "eta_etc": "eta_etc",
    "stress_days": "dias_ks_menor_1",
    "ks_min": "ks_min",
    "irrigations": "riegos",
    "closure_mm": "cierre_mm",
}
CLIMATE_COLUMNS = {
    "comparison": "comparacion",
    "period": "temporada",
    "n_days": "dias",
    "reference_mm": "referencia_media_mm",
    "estimate_mm": "estimada_media_mm",
    "mean_diff_mm": "diferencia_media_mm",
    "rmse_mm": "rmse_mm",
    "era5_mm": "era5_mm",
    "reference_mean_mm": "referencia_media_mm",
    "reference_min_mm": "referencia_minimo_mm",
    "reference_max_mm": "referencia_maximo_mm",
    "diff_mm": "diferencia_mm",
    "diff_pct": "diferencia_pct",
    "percentile": "percentil",
    "ifs_mm": "ifs_mm",
}

Row = dict[str, object]


@dataclass(frozen=True)
class Case:
    """Un caso de la simulacion. En los gemelos, el suelo y p son los que usa el sistema
    para decidir; el escenario indica que cambia en el balance real."""
    analysis: str
    season: str
    soil: SoilType = SOIL
    p: float = P
    scenario: str = NO_ERROR
    every: int = 1 # dias entre consultas

    def columns(self) -> Row:
        return {"analisis": self.analysis, "temporada": self.season, "suelo": self.soil.value,
                "p": self.p, "escenario": self.scenario, "consulta_cada_dias": self.every}

@dataclass(frozen=True)
class CaseResult:
    """Promedio, minimo y maximo de las mediciones de cada estrategia en un caso: del
    sistema entre los dias de inicio de las consultas y de los calendarios entre sus
    fechas de inicio, para cada intervalo."""
    case: Case
    system: dict[str, Metrics]
    planned: dict[int, dict[str, Metrics]]
    same_water: dict[int, dict[str, Metrics]]

def run_case(case: Case, system_runs: list[Metrics], requirement: list[float], real: Step) -> CaseResult:
    """Corre los calendarios del caso sobre el balance real y resume las corridas."""
    system = summarize(system_runs)
    # calendario a igual agua: agua neta del sistema en el caso (con varias corridas, la media)
    net_mm = system["promedio"].net_mm
    return CaseResult(
        case=case,
        system=system,
        planned={iv: summarize(calendar_runs(iv, requirement, real)) for iv in CALENDAR_INTERVALS},
        same_water={iv: summarize(calendar_runs(iv, requirement, real, net_mm)) for iv in CALENDAR_INTERVALS},
    )


def sensitivity(seasons: dict[str, list[Day]], requirements: dict[str, list[float]]) -> list[CaseResult]:
    """Seccion 8: las nueve configuraciones de suelo y p en cada temporada; el sistema
    conoce los parametros correctos."""
    results = []
    for label, days in seasons.items():
        for soil in SOILS:
            for p in PS:
                real = system_balance(days, soil, p)
                runs = query_runs(1, BalanceParams(soil=soil, p=p).raw, real, len(days))
                results.append(run_case(Case(SENSITIVITY, label, soil, p), runs, requirements[label], real))
    return results

def twins(seasons: dict[str, list[Day]], requirements: dict[str, list[float]]) -> list[CaseResult]:
    """Seccion 9: el sistema decide con su balance (parametros del caso de estudio) y
    los resultados se miden en el balance real de cada escenario."""
    raw = BalanceParams().raw
    results = []
    for label, days in seasons.items():
        estimated = system_balance(days)
        for scenario, params in SCENARIOS.items():
            real = modified_balance(days, params)
            runs = [season_metrics(simulate(len(days), threshold_rule(raw), real, estimated))]
            results.append(run_case(Case(TWINS, label, scenario=scenario), runs, requirements[label], real))
    return results

def frequency(seasons: dict[str, list[Day]], requirements: dict[str, list[float]]) -> list[CaseResult]:
    """Seccion 10: el sistema solo decide en los dias de consulta, con cada dia de inicio."""
    raw = BalanceParams().raw
    results = []
    for label, days in seasons.items():
        real = system_balance(days)
        for every in QUERY_EVERY:
            runs = query_runs(every, raw, real, len(days))
            results.append(run_case(Case(FREQUENCY, label, every=every), runs, requirements[label], real))
    return results

def check_daily_query(sensitivity_results: list[CaseResult], frequency_results: list[CaseResult]) -> None:
    """Con consulta diaria, el sistema y los calendarios de la frecuencia de consulta
    tienen que coincidir con los del caso de estudio."""
    study = {r.case.season: r for r in sensitivity_results if r.case.soil is SOIL and r.case.p == P}
    for r in frequency_results:
        if r.case.every == 1:
            s = study[r.case.season]
            assert (r.system, r.planned, r.same_water) == (s.system, s.planned, s.same_water), (
                f"{r.case.season}: la consulta diaria no coincide con el caso de estudio")


def metric_rows(r: CaseResult) -> list[Row]:
    """Todas las mediciones del caso: promedio, minimo y maximo de cada estrategia e intervalo."""
    strategies: list[tuple[str, int | None, dict[str, Metrics]]] = [(SYSTEM, None, r.system)]
    strategies += [(PLANNED, iv, summary) for iv, summary in r.planned.items()]
    strategies += [(SAME_WATER, iv, summary) for iv, summary in r.same_water.items()]
    return [{**r.case.columns(), "estrategia": name, "intervalo_dias": iv, "estadistico": stat,
             **{METRIC_COLUMNS[k]: v for k, v in asdict(m).items()}}
            for name, iv, summary in strategies for stat, m in summary.items()]

def strategy_columns(strategy: str, m: Metrics) -> Row:
    return {f"percolacion_{strategy}_mm": m.perc_mm, f"eta_etc_{strategy}": eta_etc(m),
            f"dias_ks_menor_1_{strategy}": m.stress_days, f"ks_min_{strategy}": m.ks_min}

def comparison_rows(r: CaseResult) -> list[Row]:
    """Seccion 6: el sistema frente a cada calendario, con el promedio de las fechas de inicio."""
    system = r.system["promedio"]
    rows: list[Row] = []
    for iv in CALENDAR_INTERVALS:
        planned, same = r.planned[iv]["promedio"], r.same_water[iv]["promedio"]
        diff = water_difference(system, planned)
        rows.append({
            **r.case.columns(),
            "intervalo_dias": iv,
            "dif_agua_total_mm": diff.total_mm,
            "dif_agua_total_pct": diff.total_pct,
            "dif_percolacion_mm": diff.perc_mm,
            "dif_eta_mm": diff.eta_mm,
            **strategy_columns("sistema", system),
            **strategy_columns("planificado", planned),
            **strategy_columns("igual_agua", same),
        })
    return rows

def criterion_row(r: CaseResult) -> Row:
    """Seccion 7: las tres condiciones del criterio, con la ETa/ETc del calendario planificado."""
    system = r.system["promedio"]
    planned = {iv: summary["promedio"] for iv, summary in r.planned.items()}
    c = criterion(system, planned)
    # margen de cada condicion (sistema - umbral o calendario): la 1 se cumple con margen >= 0,
    # la 2 con margen < 0 y la 3 con margen <= 0
    return {
        **r.case.columns(),
        "eta_etc_sistema": eta_etc(system),
        "cond1_eta_etc": c.crop,
        "margen_cond1_eta_etc": round(eta_etc(system) - ETA_ETC_MIN, 3),
        "eta_etc_uva_de_mesa": c.crop_table_grape,
        "cond2_agua_total": c.water,
        "margen_cond2_agua_total_mm": system.total_mm - min(m.total_mm for m in planned.values()),
        "cond3_percolacion": c.percolation,
        "margen_cond3_percolacion_mm": system.perc_mm - min(m.perc_mm for m in planned.values()),
        "favorable": c.favorable,
        **{f"eta_etc_planificado_{iv}d": eta_etc(m) for iv, m in planned.items()},
    }

def requirement_rows(seasons: dict[str, list[Day]],
                     planned: dict[str, list[MonthRequirement]]) -> list[Row]:
    """Requerimiento medio de cada mes (seccion 4.2) frente al de la temporada, calculado con
    sus propios datos. La ultima columna es el requerimiento con la formula de la simulacion
    exploratoria de junio (suma dia por dia), que no se usa en la simulacion final."""
    rows: list[Row] = []
    for label, days in seasons.items():
        june = daily_sum_requirement(days)
        for mean_req, own in zip(planned[label], season_requirement(days)):
            rows.append({
                "temporada": label,
                "mes": mean_req.month,
                "kc_medio": mean_req.kc,
                "eto_media_mm": mean_req.eto_mm,
                "pe_media_mm": mean_req.pe_mm,
                "requerimiento_medio_mm": mean_req.requirement_mm,
                "kc_temporada": own.kc,
                "eto_temporada_mm": own.eto_mm,
                "pe_temporada_mm": own.pe_mm,
                "requerimiento_temporada_mm": own.requirement_mm,
                "requerimiento_formula_junio_mm": june[mean_req.month],
            })
    return rows

def climate_tables(seasons: dict[str, list[Day]]) -> dict[str, pd.DataFrame]:
    """Seccion 11 y correccion (c) de la seccion 13: la verificacion de la ETo y la caracterizacion
    climatica. La lluvia frente a las estaciones no va a los resultados (el motivo esta en el README);
    se ve con el diagnostico de climate_check."""
    def frame(rows: list) -> pd.DataFrame:
        return pd.DataFrame([asdict(x) for x in rows]).rename(columns=CLIMATE_COLUMNS)

    return {
        "verificacion_eto.csv": frame(verify_eto(seasons)),
        "caracterizacion_climatica.csv": frame(characterize(seasons)),
    }


def write(name: str, table: pd.DataFrame) -> None:
    # 6 cifras significativas; el control de cierre queda visible aunque sea cercano a 0
    table.to_csv(OUT_DIR / name, index=False, float_format="%.6g")
    print(f"  _out/{name}: {len(table)} filas")

def main() -> None:
    print(f"Ubicacion: {SECTOR_FILE.name}")
    seasons = load_seasons()
    climate = load_climate_series()
    planned = {label: planned_requirement(label, seasons, climate) for label in seasons}
    requirements = {label: daily_requirement(days, planned[label]) for label, days in seasons.items()}

    sens = sensitivity(seasons, requirements)
    twin = twins(seasons, requirements)
    freq = frequency(seasons, requirements)
    check_daily_query(sens, freq)
    results = sens + twin + freq

    OUT_DIR.mkdir(exist_ok=True)
    measurements = pd.DataFrame([row for r in results for row in metric_rows(r)])
    write("mediciones.csv", measurements)
    write("comparacion.csv", pd.DataFrame([row for r in results for row in comparison_rows(r)]))
    criteria = pd.DataFrame([criterion_row(r) for r in results])
    write("criterio.csv", criteria)
    write("requerimiento.csv", pd.DataFrame(requirement_rows(seasons, planned)))
    for name, table in climate_tables(seasons).items():
        write(name, table)

    # minimo y maximo de cada caso, estrategia e intervalo cubren todas las corridas
    print(f"\nMayor residuo del cierre del balance (todas las corridas): "
          f"{measurements['cierre_mm'].abs().max():.1e} mm")
    print("\nCasos favorables:")
    for analysis, group in criteria.groupby("analisis", sort=False):
        print(f"  {analysis}: {int(group['favorable'].sum())} de {len(group)}")

if __name__ == "__main__":
    main()