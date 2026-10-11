"""
Estudio de eficiencia hídrica (validación de tesis).

Simula sobre clima ERA5 + NDVI Sentinel-2 REALES del sector Malbec (San Rafael)
con el MISMO motor FAO-56, comparando una política de SISTEMA contra dos
baselines de CALENDARIO que separan los dos efectos en juego:
- SISTEMA (just-in-time): riega cuando Dr >= RAW y repone a capacidad de campo.
- CALENDARIO@IRN: fechas fijas {7,10,14} d, lámina dosada al requerimiento neto
    estacional (IRN). Mide cuánto MENOS AGUA usa el sistema.
- CALENDARIO@sistema: mismas fechas fijas, dosado a la MISMA agua neta que aplicó
    el sistema. Aísla el TIMING puro (misma agua, ¿quién la reparte mejor?).

Mide por temporada y política: agua aplicada, percolación profunda (desperdicio)
y días de estrés (Ks<1). Reusa funciones puras del backend; NO toca la DB.

Uso (desde backend/):   venv/Scripts/python.exe scripts/sim_efficiency.py
"""
from __future__ import annotations
import json
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permitir import app.*

import pandas as pd

from app.models.enums import CropType, HailNetType, SoilType
from app.schemas.climate import ClimateData
from app.schemas.satellite import SatelliteData
from app.ingestion.climate import get_climate_data_for_range
from app.ingestion.satellite import get_satellite_indices_for_range
from app.calculation.eto import calculate_eto
from app.calculation.kc import calculate_kc
from app.calculation import water_balance as wb

# CONFIG (sector Malbec real, fijado) 
SECTOR_NAME = "Malbec"
CROP        = CropType.vine
HAIL_NET    = HailNetType.open          # malla abierta: el NDVI se usa
SOIL        = SoilType.sandy_loam       # SoilGrids 0-5cm -> TAW=150, RAW=67.5
ROOT_DEPTH  = 1.5
P_DEFAULT   = 0.45
EFFICIENCY  = 0.85                       # aspersión (FAO-56: 85-90%)

# Ubicación del sector: no se versiona (el repositorio es público). Se lee de
# sector_local.json; si no está, de sector_local.example.json (coordenadas
# redondeadas a 0,1° y sin polígono), que alcanza para reproducir desde _cache/.
_SECTOR_FILE = Path(__file__).resolve().parent / "sector_local.json"
if not _SECTOR_FILE.exists():
    _SECTOR_FILE = _SECTOR_FILE.with_name("sector_local.example.json")
    print(f"Aviso: sin sector_local.json, se usa {_SECTOR_FILE.name} "
          "(coordenadas redondeadas)", file=sys.stderr)
_SECTOR  = json.loads(_SECTOR_FILE.read_text(encoding="utf-8"))
LAT, LON = _SECTOR["lat"], _SECTOR["lon"]
POLYGON  = _SECTOR["polygon"]             # null en el archivo de ejemplo

SEASONS = [   # temporada de riego: 1-sep (brotación) -> 30-abr
    (date(2021, 9, 1), date(2022, 4, 30)),
    (date(2022, 9, 1), date(2023, 4, 30)),
    (date(2023, 9, 1), date(2024, 4, 30)),
]
CALENDAR_INTERVALS = [7, 10, 14]
NDVI_MAX_AGE = 15                        # mismo criterio de vigencia que el sistema
CACHE_DIR = Path(__file__).resolve().parent / "_cache"
OUT_DIR   = Path(__file__).resolve().parent / "_out"


# capa de datos (con cache)
def _fetch_raw(start: date, end: date) -> dict:
    """Clima ERA5 + NDVI S2 reales, cacheados en JSON por temporada."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache = CACHE_DIR / f"{SECTOR_NAME}_{start}_{end}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    if POLYGON is None:
        sys.exit(f"Falta _cache/{cache.name} y no hay polígono del sector "
                 "(sector_local.json no se versiona). La simulación se reproduce "
                 "a partir de los datos guardados en _cache/; no se descargan.")
    clim = get_climate_data_for_range(LAT, LON, start, end)
    imgs = get_satellite_indices_for_range(POLYGON, start - timedelta(days=NDVI_MAX_AGE), end)
    data = {
        "climate": {d.isoformat(): c.model_dump(mode="json") for d, c in clim.items()},
        "ndvi": [[i.image_date.isoformat(), i.ndvi] for i in imgs],
    }
    cache.write_text(json.dumps(data), encoding="utf-8")
    return data


@dataclass
class Day:
    d: date
    eto: object          # EToResult
    kc: object           # KcResult
    precip_mm: float
    etc_mm: float
    pe_mm: float


def build_series(start: date, end: date) -> list[Day]:
    raw = _fetch_raw(start, end)
    clim = {date.fromisoformat(k): ClimateData(**v) for k, v in raw["climate"].items()}
    imgs = sorted((date.fromisoformat(k), nd) for k, nd in raw["ndvi"])

    def ndvi_for(day: date):
        cand = [nd for dt, nd in imgs if dt <= day and (day - dt).days <= NDVI_MAX_AGE]
        return cand[-1] if cand else None

    series, d = [], start
    while d <= end:
        c = clim.get(d)
        if c is not None:
            eto = calculate_eto(c, LAT, d)
            nd = ndvi_for(d)
            sat = (SatelliteData(sector_id=0, date=d, ndvi=nd, cloud_cover_pct=0.0)
                    if nd is not None else None)
            kc = calculate_kc(CROP, d, sat, HAIL_NET)
            series.append(Day(d, eto, kc, c.precipitation_mm,
                            kc.kc * eto.eto_mm, wb.effective_precipitation(c.precipitation_mm)))
        d += timedelta(days=1)
    return series


def season_irn(series: list[Day]) -> float:
    """Requerimiento neto de riego FAO-56 = Σ max(0, ETc - Pe). Óptimo físico."""
    return sum(max(0.0, x.etc_mm - x.pe_mm) for x in series)


# motor de simulación
def run_policy(series, decide, p=P_DEFAULT, soil=SOIL, root=ROOT_DEPTH, eff=EFFICIENCY) -> dict:
    s = wb._SOIL_PROPS[soil]
    taw = 1000 * (s["theta_fc"] - s["theta_wp"]) * root
    raw = p * taw

    deficit = 0.0                          # arranca a capacidad de campo
    net = gross = dp = 0.0
    stress = severe = 0
    for i, x in enumerate(series):
        irr = decide(i, deficit, raw, taw)
        res = wb.calculate_water_balance(x.eto, x.kc, x.precip_mm, deficit,
                                        soil, root, p, irrigation_mm=irr)
        deficit = res.water_deficit_mm
        net += irr
        gross += irr / eff
        dp += res.deep_percolation_mm
        stress += res.ks < 1.0
        severe += res.ks < 0.5
    return dict(neto_mm=net, bruto_mm=gross, percolacion_mm=dp,
                dias_sed=stress, dias_sed_severo=severe)


def decide_system(i, deficit, raw, taw):
    return deficit if deficit >= raw else 0.0       # repone a FC al cruzar RAW


def make_calendar(interval, total_net, n_days, phase):
    irr_days = set(range(phase, n_days, interval))
    d_net = total_net / len(irr_days)
    return lambda i, deficit, raw, taw: (d_net if i in irr_days else 0.0)

# sensibilidad (p × suelo)
P_GRID = [0.40, 0.45, 0.50]
SOIL_GRID = [SoilType.loamy_sand, SoilType.sandy_loam, SoilType.loam]  # base ±1 clase textural


def _dominates(a: dict, b: dict) -> bool:
    """Test de dominancia de Pareto: a domina a b si a <= b en los 3 ejes
    (agua, perc, sed) y < en al menos uno. Menor es mejor en los tres."""
    axes = ("neto_mm", "percolacion_mm", "dias_sed")
    le = all(a[k] <= b[k] for k in axes)
    lt = any(a[k] < b[k] for k in axes)
    return le and lt


def sweep_sensitivity():
    """Corre la comparación sistema-vs-calendarios en la grilla p × suelo y verifica que el
    sistema sea Pareto-óptimo (no superado por ninguna variante de calendario) en cada config."""
    OUT_DIR.mkdir(exist_ok=True)
    series_by_season = {(s, e): build_series(s, e) for s, e in SEASONS}  # cache de datos

    rows, summary = [], []
    for p in P_GRID:
        for soil in SOIL_GRID:
            sp = wb._SOIL_PROPS[soil]
            taw = 1000 * (sp["theta_fc"] - sp["theta_wp"]) * ROOT_DEPTH
            cfg = f"p={p:.2f}/{soil.value}"
            all_pareto, savings = True, []

            for (start, end), series in series_by_season.items():
                tag = f"{start.year}/{str(end.year)[2:]}"
                irn, n = season_irn(series), len(series)

                m_sys = run_policy(series, decide_system, p=p, soil=soil)
                sys_net = m_sys["neto_mm"]

                calendars = []
                for itv in CALENDAR_INTERVALS:
                    for total, lbl in ((irn, "IRN"), (sys_net, "sistema")):
                        phases = [run_policy(series, make_calendar(itv, total, n, ph),
                                            p=p, soil=soil) for ph in range(itv)]
                        agg = {k: sum(pm[k] for pm in phases) / len(phases) for k in phases[0]}
                        calendars.append((f"cal@{lbl}/{itv}d", agg))

                superado_por = [lbl for lbl, c in calendars if _dominates(c, m_sys)]
                pareto_ok = not superado_por
                all_pareto &= pareto_ok
                savings.append(100 * (irn - sys_net) / irn if irn > 0 else 0.0)

                rows.append(dict(
                    config=cfg, TAW=round(taw), temporada=tag,
                    sis_agua=round(sys_net, 1), sis_perc=round(m_sys["percolacion_mm"], 1),
                    sis_sed=round(m_sys["dias_sed"], 1),
                    pareto_optimo="sí" if pareto_ok else "NO (superado por: " + ", ".join(superado_por) + ")",
                ))

            summary.append(dict(
                config=cfg, TAW=round(taw),
                pareto_optimo_3temp="sí" if all_pareto else "NO",
                ahorro_agua_pct=f"{min(savings):.0f}-{max(savings):.0f}",
            ))

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "sim_sweep.csv", index=False)
    sm = pd.DataFrame(summary)
    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 20)
    print("=== Sensibilidad: detalle por config × temporada ===")
    print(df.to_string(index=False))
    print("\n=== Resumen por config (¿Pareto-óptimo en las 3 temporadas?) ===")
    print(sm.to_string(index=False))
    print(f"\nCSV -> {OUT_DIR / 'sim_sweep.csv'}")

# runner
def main():
    OUT_DIR.mkdir(exist_ok=True)
    rows = []
    for start, end in SEASONS:
        tag = f"{start.year}/{str(end.year)[2:]}"
        series = build_series(start, end)
        irn, n = season_irn(series), len(series)

        # SISTEMA (just-in-time: gatilla en RAW, repone a FC)
        m_sys = run_policy(series, decide_system)
        sys_net = m_sys["neto_mm"]
        rows.append(dict(temporada=tag, politica="sistema", intervalo="-",
                        IRN_mm=round(irn), **{k: round(v, 1) for k, v in m_sys.items()}))

        for itv in CALENDAR_INTERVALS:
            # Baseline A: calendario dosado al IRN -> "el sistema usa menos agua"
            phases = [run_policy(series, make_calendar(itv, irn, n, ph)) for ph in range(itv)]
            agg = {k: sum(pm[k] for pm in phases) / len(phases) for k in phases[0]}
            rows.append(dict(temporada=tag, politica="calendario@IRN", intervalo=f"{itv}d",
                            IRN_mm=round(irn), **{k: round(v, 1) for k, v in agg.items()}))

            # Baseline B: calendario dosado a la MISMA agua que el sistema -> timing puro
            phases = [run_policy(series, make_calendar(itv, sys_net, n, ph)) for ph in range(itv)]
            agg = {k: sum(pm[k] for pm in phases) / len(phases) for k in phases[0]}
            rows.append(dict(temporada=tag, politica="calendario@sistema", intervalo=f"{itv}d",
                            IRN_mm=round(irn), **{k: round(v, 1) for k, v in agg.items()}))
            
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "sim_results.csv", index=False)
    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 20)
    print(df.to_string(index=False))
    print(f"\nCSV -> {OUT_DIR / 'sim_results.csv'}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sweep":
        sweep_sensitivity()
    else:
        main()