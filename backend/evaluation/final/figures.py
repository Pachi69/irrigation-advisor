"""
Figuras de la simulación final de eficiencia hídrica (sección 12 del protocolo).

Lee los resultados de evaluation/final/_out/ (antes hay que correr run.py) y guarda
las figuras en evaluation/final/_out/figuras/:
- figura_a_agotamiento.png: evolución del agotamiento del sistema y del calendario
  planificado en cada temporada, con la lluvia diaria.
- figura_b_agua_percolacion_eta_etc.png: agua total, percolación y ETc aj/ETc del
  sistema y de los calendarios en cada temporada.
- figura_c_requerimiento.png: requerimiento medio frente al de cada temporada.
- figura_d_sensibilidad.png, figura_e_errores.png y figura_f_frecuencia.png:
  márgenes del criterio en los análisis de sensibilidad, de errores y de
  frecuencia de consulta.
En las figuras A y B, el calendario de cada temporada es el del intervalo con menor
agua total media. Los otros intervalos van en figuras complementarias con el mismo
formato (por ejemplo, figura_a_agotamiento_10d.png).

La figura A necesita el agotamiento día por día, que no está en los CSV: vuelve a
simular el caso de estudio con las mismas funciones que run.py y verifica que el
agua total coincida con la de mediciones.csv.

Uso (desde backend/):  venv/Scripts/python.exe -m evaluation.final.figures
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

import matplotlib
matplotlib.use("Agg") # sin pantalla, solo archivos
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter

from .balance import BalanceParams, Step, system_balance
from .comparison import ETA_ETC_MIN, ETA_ETC_TABLE_GRAPE
from .data import P, SOIL, Day, daily_requirement, load_climate_series, load_seasons, planned_requirement
from .run import (FREQUENCY, NO_ERROR, OUT_DIR, PLANNED, PS, QUERY_EVERY, SAME_WATER, SCENARIOS, SENSITIVITY,
                  SOILS, SYSTEM, TWINS)
from .strategies import CALENDAR_INTERVALS, calendar, calendar_runs, planned_doses, simulate, threshold_rule

FIG_DIR = OUT_DIR / "figuras"
DPI = 300

# Colores de las estrategias (los mismos de la simulacion exploratoria)
C_SYSTEM = "#1b7f5c"
C_PLANNED = "#e07b39"
C_SAME_WATER = "#8a8d91"
C_SEASON_REQUIREMENT = "#4d4d4d"
C_RAIN = "#3b7dbf"
C_MEETS = "#ececec" # zona donde se cumple una condicion del criterio
# Marcador de cada temporada en las figuras E y F (en orden de temporada)
SEASON_STYLES = [("#0072B2", "o"), ("#CC79A7", "s"), ("#222222", "^")]

MONTHS = {1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
          7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"}
MONTH_NAMES = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio", 7: "julio",
               8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}
SOIL_LABELS = {"loamy_sand": "arenoso franco", "sandy_loam": "franco arenoso", "loam": "franco"}
SCENARIO_LABELS = {
    NO_ERROR: "sin error",
    "ETo mayor": "ETo mayor",
    "ETo menor": "ETo menor",
    "Kc mayor": "Kc mayor",
    "Kc menor": "Kc menor",
    "suelo mas liviano": "suelo más liviano",
    "suelo mas pesado": "suelo más pesado",
    "menos lluvia efectiva": "menos lluvia efectiva",
    "combinado: menos agua de la estimada": "combinado: menos agua\nde la estimada",
    "combinado: mas agua de la estimada": "combinado: más agua\nde la estimada",
}
# Escenarios de error en pares (mayor y menor), la lluvia sola y los combinados al final
SCENARIO_GROUPS = [
    ["ETo mayor", "ETo menor"],
    ["Kc mayor", "Kc menor"],
    ["suelo mas liviano", "suelo mas pesado"],
    ["menos lluvia efectiva"],
    ["combinado: menos agua de la estimada", "combinado: mas agua de la estimada"],
]


def num(x: float, decimals: int = 1, sign: bool = False) -> str:
    """Numero con coma decimal y signo menos tipografico; con sign, tambien el signo +."""
    text = f"{x:+.{decimals}f}" if sign else f"{x:.{decimals}f}"
    return text.replace(".", ",").replace("-", "−")

def decimal_comma(ax: Axes, decimals: int, axis: str = "y") -> None:
    formatter = FuncFormatter(lambda v, _: num(v, decimals))
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(formatter)

def add_legend(fig: Figure, handles: list, ncol: int) -> None:
    """Leyenda debajo de los graficos. Se ancla en coordenadas de la figura para que no se
    mueva al recortar los margenes al guardar."""
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.005),
               bbox_transform=fig.transFigure, ncol=ncol, frameon=False)

def save(fig: Figure, name: str) -> None:
    fig.savefig(FIG_DIR / name, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  _out/figuras/{name}")


def read(name: str) -> pd.DataFrame:
    path = OUT_DIR / name
    if not path.exists():
        sys.exit(f"Falta _out/{name}: antes hay que correr evaluation.final.run")
    return pd.read_csv(path)

def one(table: pd.DataFrame, **match: object) -> pd.Series:
    """La unica fila de la tabla con los valores indicados."""
    rows = table
    for column, wanted in match.items():
        rows = rows[rows[column] == wanted]
    if len(rows) != 1:
        raise ValueError(f"se esperaba una fila con {match} y hay {len(rows)}")
    return rows.iloc[0]

def value(table: pd.DataFrame, column: str, **match: object) -> float:
    return float(one(table, **match)[column])

def study_case(table: pd.DataFrame) -> pd.DataFrame:
    """Filas del caso de estudio (franco arenoso, p 0,45) en el analisis de sensibilidad."""
    return table[(table["analisis"] == SENSITIVITY) & (table["suelo"] == SOIL.value) & (table["p"] == P)]

def cheapest_interval(measurements: pd.DataFrame, season: str) -> int:
    """Intervalo del calendario planificado con menor agua total media en la temporada."""
    return min(CALENDAR_INTERVALS, key=lambda iv: value(
        measurements, "agua_total_mm", temporada=season, estrategia=PLANNED, intervalo_dias=iv,
        estadistico="promedio"))

def check(simulated: float, measurements: pd.DataFrame, what: str, **match: object) -> None:
    expected = value(measurements, "agua_total_mm", estadistico="promedio", **match)
    if abs(simulated - expected) > 0.01:
        sys.exit(f"{what}: agua total {simulated:.3f} mm frente a {expected:.3f} mm en mediciones.csv; "
                 "hay que volver a correr evaluation.final.run")


# ---------- Figura A: evolucion del agotamiento ----------
def calendar_depletion(real: Step, requirement: list[float], interval: int) -> tuple[int, float, list[float]]:
    """Calendario planificado con la fecha de inicio cuya agua total es la mas cercana a la
    media entre fechas de inicio: dia del primer riego, agua total media y agotamiento diario."""
    totals = [m.total_mm for m in calendar_runs(interval, requirement, real)] # indice = dia de inicio
    mean_total = sum(totals) / len(totals)
    first = min(range(interval), key=lambda f: abs(totals[f] - mean_total))
    run = simulate(len(requirement), calendar(planned_doses(interval, first, requirement)), real)
    return first, mean_total, [r.dr for r in run]

def figure_a(seasons: dict[str, list[Day]], requirements: dict[str, list[float]],
             measurements: pd.DataFrame, interval: int | None = None) -> None:
    """Sin intervalo, figura principal: en cada temporada, el calendario del intervalo con menor
    agua total media. Con un intervalo, figura complementaria con ese intervalo en todas."""
    intervals = {label: interval or cheapest_interval(measurements, label) for label in seasons}
    params = BalanceParams()
    rain_max = max(x.precip_mm for days in seasons.values() for x in days)
    fig = plt.figure(figsize=(11, 3.4 * len(seasons)), layout="constrained")
    outer = fig.add_gridspec(len(seasons), 1)
    for i, (label, days) in enumerate(seasons.items()):
        real = system_balance(days)
        system = simulate(len(days), threshold_rule(params.raw), real)
        check(sum(r.irrigation for r in system) + system[-1].dr, measurements, f"{label} sistema",
              temporada=label, estrategia=SYSTEM)
        iv = intervals[label]
        first, mean_total, planned = calendar_depletion(real, requirements[label], iv)
        check(mean_total, measurements, f"{label} calendario de {iv} dias", temporada=label,
              estrategia=PLANNED, intervalo_dias=iv)

        dates = [x.date for x in days]
        sub = outer[i].subgridspec(2, 1, height_ratios=[3, 1])
        ax = fig.add_subplot(sub[0])
        ax_rain = fig.add_subplot(sub[1], sharex=ax)
        ax.plot(dates, [r.dr for r in system], color=C_SYSTEM, lw=1.5)
        ax.plot(dates, planned, color=C_PLANNED, lw=1.3)
        ax.axhline(params.raw, color="#333333", ls="--", lw=0.9)
        ax.axhline(params.taw, color="#333333", ls=":", lw=0.9)
        ax.set_ylim(params.taw + 6, -4) # eje invertido: arriba, capacidad de campo
        ax.set_ylabel("Agotamiento (mm)\n0 = capacidad de campo")
        start = days[first].date
        ax.set_title(f"{label}: calendario planificado cada {iv} días, primer riego el "
                     f"{start.day} de {MONTH_NAMES[start.month]}", loc="left", fontsize=10, fontweight="bold")
        ax.grid(alpha=0.3)
        ax.tick_params(labelbottom=False)

        ax_rain.bar(dates, [x.precip_mm for x in days], width=1.0, color=C_RAIN)
        ax_rain.set_ylim(0, rain_max * 1.05)
        ax_rain.set_ylabel("Lluvia\n(mm)")
        ax_rain.set_xlim(dates[0], dates[-1])
        ax_rain.xaxis.set_major_locator(mdates.MonthLocator())
        ax_rain.xaxis.set_major_formatter(FuncFormatter(lambda v, _: MONTHS[mdates.num2date(v).month]))
        ax_rain.grid(alpha=0.3)

    handles = [Line2D([], [], color=C_SYSTEM, lw=1.5, label="sistema"),
               Line2D([], [], color=C_PLANNED, lw=1.3, label="calendario planificado"),
               Line2D([], [], color="#333333", ls="--", lw=0.9, label=f"RAW = {num(params.raw)} mm"),
               Line2D([], [], color="#333333", ls=":", lw=0.9, label=f"TAW = {num(params.taw, 0)} mm"),
               Patch(color=C_RAIN, label="lluvia diaria total")]
    add_legend(fig, handles, 5)
    save(fig, f"figura_a_agotamiento{f'_{interval}d' if interval else ''}.png")


# ---------- Figura B: agua total, percolacion y ETc aj/ETc ----------
@dataclass(frozen=True)
class Stat:
    mean: float
    low: float
    high: float

def stat(measurements: pd.DataFrame, column: str, **match: object) -> Stat:
    return Stat(*(value(measurements, column, estadistico=s, **match) for s in ("promedio", "minimo", "maximo")))

def whisker(ax: Axes, x: float, s: Stat) -> None:
    """Bigote del minimo al maximo alrededor del promedio."""
    ax.errorbar(x, s.mean, yerr=[[s.mean - s.low], [s.high - s.mean]], fmt="none", ecolor="#333333",
                elinewidth=1, capsize=3, clip_on=False)

def figure_b(labels: list[str], measurements: pd.DataFrame, interval: int | None = None) -> None:
    """Sin intervalo, figura principal: en cada temporada, los calendarios del intervalo con menor
    agua total media. Con un intervalo, figura complementaria con ese intervalo en todas."""
    intervals = {label: interval or cheapest_interval(measurements, label) for label in labels}
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), layout="constrained")
    ax_total, ax_perc, ax_eta = axes
    width = 0.26
    strategies = [(SYSTEM, C_SYSTEM), (PLANNED, C_PLANNED), (SAME_WATER, C_SAME_WATER)]
    for i, label in enumerate(labels):
        for k, (strategy, color) in enumerate(strategies):
            x = i + (k - 1) * width
            match: dict[str, object] = {"temporada": label, "estrategia": strategy}
            if strategy != SYSTEM:
                match["intervalo_dias"] = intervals[label]
            net = stat(measurements, "riego_neto_mm", **match)
            final = stat(measurements, "agotamiento_final_mm", **match)
            total = stat(measurements, "agua_total_mm", **match)
            perc = stat(measurements, "percolacion_mm", **match)
            eta = stat(measurements, "eta_etc", **match)
            ax_total.bar(x, net.mean, width, color=color)
            ax_total.bar(x, final.mean, width, bottom=net.mean, color=color, alpha=0.45, hatch="///",
                         edgecolor="white", linewidth=0)
            ax_perc.bar(x, perc.mean, width, color=color)
            ax_eta.plot(x, eta.mean, marker="o", ms=7, color=color, ls="none", clip_on=False, zorder=3)
            if strategy != SYSTEM:
                whisker(ax_total, x, total)
                whisker(ax_perc, x, perc)
                whisker(ax_eta, x, eta)

    ticks = [f"{label}\ncada {intervals[label]} días" for label in labels]
    for ax, title in ((ax_total, "Agua total (mm)"), (ax_perc, "Percolación (mm)"), (ax_eta, "ETc aj/ETc")):
        ax.set_title(title, fontweight="bold")
        ax.set_xticks(range(len(labels)), ticks)
        ax.grid(axis="y", alpha=0.3)
    ax_eta.set_ylim(0.60, 1.00)
    decimal_comma(ax_eta, 2)
    ax_eta.axhline(ETA_ETC_MIN, color="#333333", ls="--", lw=1)
    ax_eta.axhline(ETA_ETC_TABLE_GRAPE, color="#333333", ls=":", lw=1)

    handles = [Patch(color=C_SYSTEM, label="sistema"),
               Patch(color=C_PLANNED, label="calendario planificado"),
               Patch(color=C_SAME_WATER, label="calendario a igual agua (comparador diagnóstico)"),
               Patch(facecolor="#999999", alpha=0.45, hatch="///", edgecolor="white",
                     label="agotamiento final (sobre el riego neto)")]
    add_legend(fig, handles, 4)
    save(fig, f"figura_b_agua_percolacion_eta_etc{f'_{interval}d' if interval else ''}.png")


# ---------- Figura C: requerimiento medio frente al de cada temporada ----------
def figure_c(labels: list[str], requirement: pd.DataFrame) -> None:
    fig, axes = plt.subplots(len(labels), 1, figsize=(10, 2.9 * len(labels)), sharex=True, sharey=True,
                             layout="constrained")
    width = 0.38
    for ax, label in zip(axes, labels):
        rows = requirement[requirement["temporada"] == label]
        x = np.arange(len(rows))
        mean_req = rows["requerimiento_medio_mm"].to_numpy(dtype=float)
        own_req = rows["requerimiento_temporada_mm"].to_numpy(dtype=float)
        ax.bar(x - width / 2, mean_req, width, color=C_PLANNED)
        ax.bar(x + width / 2, own_req, width, color=C_SEASON_REQUIREMENT)
        ax.set_title(f"{label}: total medio {num(mean_req.sum())} mm; total de la temporada "
                     f"{num(own_req.sum())} mm", loc="left", fontsize=10, fontweight="bold")
        ax.set_ylabel("mm")
        ax.set_xticks(x, [MONTHS[int(m)] for m in rows["mes"]])
        ax.grid(axis="y", alpha=0.3)

    handles = [Patch(color=C_PLANNED, label="requerimiento medio (calendario planificado)"),
               Patch(color=C_SEASON_REQUIREMENT, label="requerimiento de la temporada")]
    add_legend(fig, handles, 2)
    save(fig, "figura_c_requerimiento.png")


# ---------- Figura D: sensibilidad ----------
def figure_d(labels: list[str], criteria: pd.DataFrame) -> None:
    rows = criteria[criteria["analisis"] == SENSITIVITY]
    if not rows["cond1_eta_etc"].all():
        raise ValueError("la figura D muestra solo los margenes de las condiciones 2 y 3: supone que la condicion 1 se cumple en todos los casos")
    limit = 110 # escala simetrica del margen de agua total (mm)
    fig, axes = plt.subplots(1, len(labels), figsize=(14, 4.9), layout="constrained")
    image = None
    for ax, label in zip(axes, labels):
        water = np.zeros((len(PS), len(SOILS)))
        favorable = 0
        for i, p in enumerate(PS):
            for j, soil in enumerate(SOILS):
                row = one(rows, temporada=label, suelo=soil.value, p=p)
                w, pc = float(row["margen_cond2_agua_total_mm"]), float(row["margen_cond3_percolacion_mm"])
                water[i, j] = w
                favorable += bool(row["favorable"])
                ax.text(j, i, f"agua {num(w, sign=True)}\nperc. {num(pc, sign=True)}\n"
                              f"{'favorable' if row['favorable'] else 'no favorable'}",
                        ha="center", va="center", fontsize=8.5,
                        color="white" if abs(w) > 0.6 * limit else "black")
        image = ax.imshow(water, cmap="BrBG_r", vmin=-limit, vmax=limit, aspect="auto")
        study = (PS.index(P), SOILS.index(SOIL))
        ax.add_patch(Rectangle((study[1] - 0.5, study[0] - 0.5), 1, 1, fill=False, lw=2.5, edgecolor="black"))
        ax.set_xticks(range(len(SOILS)),
                      [f"{SOIL_LABELS[s.value]}\n(TAW {num(BalanceParams(soil=s).taw, 0)} mm)" for s in SOILS])
        ax.set_yticks(range(len(PS)), [f"p = {num(p, 2)}" for p in PS])
        ax.set_title(f"{label}: {favorable} de {len(PS) * len(SOILS)} favorables", fontweight="bold")
    assert image is not None
    fig.colorbar(image, ax=axes, label="Margen de agua total (mm)", shrink=0.9)
    save(fig, "figura_d_sensibilidad.png")


# ---------- Figuras E y F: margenes por escenario y por frecuencia ----------
@dataclass(frozen=True)
class Margins:
    """Resultado del sistema en un caso: ETc aj/ETc y margenes de las condiciones 2 y 3."""
    eta_etc: Stat
    water: Stat
    perc: Stat
    favorable: bool

def single(x: float) -> Stat:
    return Stat(x, x, x)

def margins_row(row: pd.Series) -> Margins:
    return Margins(single(float(row["eta_etc_sistema"])), single(float(row["margen_cond2_agua_total_mm"])),
                   single(float(row["margen_cond3_percolacion_mm"])), bool(row["favorable"]))

def margins_figure(labels: list[str], groups: list[list[str]], row_labels: dict[str, str],
                   results: dict[tuple[str, str], Margins], name: str) -> None:
    """Tres paneles con eje y compartido (ETc aj/ETc del sistema, margen de agua total y margen de
    percolacion) y una columna con la marca de favorable de cada temporada."""
    y: dict[str, float] = {}
    pos = 0.0
    for group in groups:
        for key in group:
            y[key] = pos
            pos += 1
        pos += 0.5 # espacio entre grupos
    limit = max(max(abs(m.water.low), abs(m.water.high), abs(m.perc.low), abs(m.perc.high))
                for m in results.values())
    limit = 10 * np.ceil(limit * 1.08 / 10)

    fig, axes = plt.subplots(1, 4, figsize=(14, 0.55 * len(y) + 2.2), sharey=True, layout="constrained",
                             gridspec_kw={"width_ratios": [1, 1, 1, 0.6]})
    ax_eta, ax_water, ax_perc, ax_fav = axes
    ax_eta.axvspan(ETA_ETC_MIN, 1.0, color=C_MEETS, zorder=0)
    ax_eta.axvline(ETA_ETC_MIN, color="#333333", ls="--", lw=1)
    ax_eta.axvline(ETA_ETC_TABLE_GRAPE, color="#333333", ls=":", lw=1)
    eta_min = min(m.eta_etc.low for m in results.values())
    ax_eta.set_xlim(min(0.60, np.floor((eta_min - 0.01) * 20) / 20), 1.00)
    decimal_comma(ax_eta, 2, axis="x")
    for ax in (ax_water, ax_perc):
        ax.axvspan(-limit, 0, color=C_MEETS, zorder=0)
        ax.axvline(0, color="#333333", lw=1)
        ax.set_xlim(-limit, limit)
    for ax, x_text in ((ax_eta, (ETA_ETC_MIN + 1.0) / 2), (ax_water, -limit / 2), (ax_perc, -limit / 2)):
        ax.text(x_text, -0.75, "cumple", ha="center", va="center", fontsize=9, color="#555555")
        ax.grid(axis="x", alpha=0.3)

    for k, label in enumerate(labels):
        color, marker = SEASON_STYLES[k]
        dy = (k - 1) * 0.22
        for key, pos in y.items():
            m = results[(label, key)]
            for ax, s in ((ax_eta, m.eta_etc), (ax_water, m.water), (ax_perc, m.perc)):
                if s.high > s.low:
                    ax.errorbar(s.mean, pos + dy, xerr=[[s.mean - s.low], [s.high - s.mean]], fmt="none",
                                ecolor=color, elinewidth=1, capsize=2.5, clip_on=False)
                ax.plot(s.mean, pos + dy, marker=marker, ms=6, color=color, ls="none", clip_on=False, zorder=3)
            ax_fav.text(k, pos, "sí" if m.favorable else "no", ha="center", va="center", fontsize=9,
                        color="black" if m.favorable else "#888888",
                        fontweight="bold" if m.favorable else "normal")

    if len(groups[0]) == 1 and len(groups) > 1: # fila de referencia separada por una linea
        for ax in axes:
            ax.axhline(y[groups[1][0]] - 0.75, color="#333333", lw=0.8)
    ax_eta.set_yticks(list(y.values()), [row_labels[key] for key in y])
    ax_eta.set_ylim(max(y.values()) + 0.6, -1.2)
    ax_eta.set_title("ETc aj/ETc del sistema", fontweight="bold")
    ax_water.set_title("Margen de agua total (mm)", fontweight="bold")
    ax_perc.set_title("Margen de percolación (mm)", fontweight="bold")
    ax_fav.set_xlim(-0.5, len(labels) - 0.5)
    ax_fav.set_xticks(range(len(labels)), labels, fontsize=8)
    ax_fav.xaxis.tick_top()
    ax_fav.tick_params(left=False, top=False)
    for spine in ax_fav.spines.values():
        spine.set_visible(False)
    ax_fav.set_title("Favorable", fontweight="bold")

    handles = [Line2D([], [], color=c, marker=mk, ls="none", ms=6, label=label)
               for label, (c, mk) in zip(labels, SEASON_STYLES)]
    add_legend(fig, handles, len(labels))
    save(fig, name)

def figure_e(labels: list[str], criteria: pd.DataFrame) -> None:
    twins = criteria[criteria["analisis"] == TWINS]
    reference = study_case(criteria)
    results: dict[tuple[str, str], Margins] = {}
    for label in labels:
        results[(label, NO_ERROR)] = margins_row(one(reference, temporada=label))
        for scenario in SCENARIOS:
            results[(label, scenario)] = margins_row(one(twins, temporada=label, escenario=scenario))
    margins_figure(labels, [[NO_ERROR]] + SCENARIO_GROUPS, SCENARIO_LABELS, results, "figura_e_errores.png")

def figure_f(labels: list[str], criteria: pd.DataFrame, measurements: pd.DataFrame) -> None:
    rows = criteria[criteria["analisis"] == FREQUENCY]
    runs = measurements[measurements["analisis"] == FREQUENCY]
    results: dict[tuple[str, str], Margins] = {}
    for label in labels:
        for every in QUERY_EVERY:
            row = one(rows, temporada=label, consulta_cada_dias=every)
            case = runs[(runs["temporada"] == label) & (runs["consulta_cada_dias"] == every)]
            system: dict[str, object] = {"estrategia": SYSTEM}
            planned = case[(case["estrategia"] == PLANNED) & (case["estadistico"] == "promedio")]
            # referencia de cada margen: el calendario mas ahorrador, el mismo en todas las frecuencias
            water_ref = float(planned["agua_total_mm"].min())
            perc_ref = float(planned["percolacion_mm"].min())
            water = stat(case, "agua_total_mm", **system)
            perc = stat(case, "percolacion_mm", **system)
            results[(label, str(every))] = Margins(
                eta_etc=stat(case, "eta_etc", **system),
                water=Stat(float(row["margen_cond2_agua_total_mm"]), water.low - water_ref, water.high - water_ref),
                perc=Stat(float(row["margen_cond3_percolacion_mm"]), perc.low - perc_ref, perc.high - perc_ref),
                favorable=bool(row["favorable"]))
    keys = [str(every) for every in QUERY_EVERY]
    margins_figure(labels, [keys], {k: f"cada {k} día{'s' if k != '1' else ''}" for k in keys}, results,
                   "figura_f_frecuencia.png")


def main() -> None:
    measurements = read("mediciones.csv")
    criteria = read("criterio.csv")
    requirement = read("requerimiento.csv")
    seasons = load_seasons()
    climate = load_climate_series()
    requirements = {label: daily_requirement(days, planned_requirement(label, seasons, climate))
                    for label, days in seasons.items()}
    labels = list(seasons)
    study = study_case(measurements)

    FIG_DIR.mkdir(exist_ok=True)
    print("Figuras:")
    figure_a(seasons, requirements, study)
    figure_b(labels, study)
    figure_c(labels, requirement)
    figure_d(labels, criteria)
    figure_e(labels, criteria)
    figure_f(labels, criteria, measurements)
    # complementarias: los intervalos que la figura principal no usa en todas las temporadas
    cheapest = {cheapest_interval(study, label) for label in labels}
    for iv in CALENDAR_INTERVALS:
        if cheapest != {iv}:
            figure_a(seasons, requirements, study, iv)
            figure_b(labels, study, iv)

if __name__ == "__main__":
    main()
