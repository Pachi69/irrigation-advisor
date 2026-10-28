"""
Datos de entrada de la simulación final de eficiencia hídrica.

Arma la serie diaria de cada temporada a partir de los datos guardados en
evaluation/_cache/, con los mismos criterios que el sistema en funcionamiento:
- ETo: la de Open-Meteo; si falta, la de Penman-Monteith propia.
- Kc: calculate_kc con el NDVI de la imagen vigente según select_image_date (la
  imagen más reciente, sin límite de antigüedad; antes de la primera imagen, esa
  imagen si está a 5 días o menos); sin imagen vigente, Kc de tabla.
También guarda la ETo de Penman-Monteith propia de todos los días, con la presión
de vapor real desde el punto de rocío [Ec. 14] y desde la humedad relativa media
[Ec. 19]. Se usan solo para comparar el cálculo propio de ETo con el de Open-Meteo.

Calcula el requerimiento medio de cada mes del calendario planificado: Kc de
las otras temporadas del estudio; ETo y precipitación efectiva de las
temporadas 2017/18 a 2023/24 sin la simulada. También calcula el requerimiento
de cada mes con los datos de cada temporada, para compararlo con el medio.

Diagnóstico (desde backend/):  venv/Scripts/python.exe -m evaluation.final.data
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from statistics import mean

import pandas as pd

from app.calculation.eto import calculate_eto
from app.calculation.kc import calculate_kc
from app.calculation.water_balance import effective_precipitation
from app.models.enums import CropType, HailNetType, KcSource, SoilType
from app.schemas.calculation import KcResult
from app.schemas.climate import ClimateData
from app.schemas.satellite import SatelliteData
from app.services.satellite import select_image_date

# Caso de estudio
SECTOR_NAME = "Malbec"
CROP = CropType.vine
HAIL_NET = HailNetType.open # malla abierta: el Kc se calcula con NDVI; densa o de color: Kc de tabla
SOIL = SoilType.sandy_loam # TAW = 150 mm
ROOT_DEPTH = 1.5
P = 0.45
EFFICIENCY = 0.85 #aspersion

SEASONS = [ # 1 de septiembre al 30 de abril
    (date(2021, 9, 1), date(2022, 4, 30)),
    (date(2022, 9, 1), date(2023, 4, 30)),
    (date(2023, 9, 1), date(2024, 4, 30)),
]
# ETo y precipitacion efectiva medias del calendario planificado: temporadas 2017/18 a 2023/24
CLIMATE_SEASONS = [(date(y, 9, 1), date(y + 1, 4, 30)) for y in range(2017, 2024)]
SEASON_MONTHS = [9, 10, 11, 12, 1, 2, 3, 4]

EVAL_DIR = Path(__file__).resolve().parents[1] # backend/evaluation
CACHE_DIR = EVAL_DIR / "_cache"
# Carpeta de _cache con los datos de Open-Meteo de la simulacion final, todos descargados el mismo dia
OPEN_METEO_DIR = "open_meteo_2026-10-17"

# Ubicacion del sector: no se versiona. Solo se usa la latitud para la ETo propia. 
# Sin sector_local.json se usa el archivo de ejemplo
SECTOR_FILE = EVAL_DIR / "sector_local.json"
if not SECTOR_FILE.exists():
    SECTOR_FILE = SECTOR_FILE.with_name("sector_local.example.json")
    print(f"Aviso: sin sector_local.json, se usa {SECTOR_FILE.name} "
          "(coordenadas redondeadas)", file=sys.stderr)
LAT = json.loads(SECTOR_FILE.read_text(encoding="utf-8"))["lat"]


@dataclass(frozen=True)
class Day:
    date: date
    eto_om_mm: float | None #ETo de Open-Meteo (None si falta)
    eto_pm_mm: float #ETo de Penman-Monteith propia, como el sistema: ea desde el punto de rocio [Ec. 14] si esta
    eto_pm_rh_mm: float #ETo de Penman-Monteith propia con ea desde la humedad relativa media [Ec. 19]
    kc: KcResult 
    precip_mm: float

    @property
    def eto_mm(self) -> float:
        """ETo que usa el sistema: Open-Meteo, con Penman-Monteith propia si falta."""
        return self.eto_om_mm if self.eto_om_mm is not None else self.eto_pm_mm

    @property
    def etc_mm(self) -> float:
        return self.kc.kc * self.eto_mm

@dataclass(frozen=True)
class MonthRequirement:
    """Requerimiento neto de un mes: max(0, Kc medio x ETo del mes - Pe del mes)."""
    month: int
    kc: float # Kc medio del mes
    eto_mm: float # ETo del mes
    pe_mm: float # precipitacion efectiva del mes

    @property
    def requirement_mm(self) -> float:
        return max(0.0, self.kc * self.eto_mm - self.pe_mm)

def season_label(start: date, end: date) -> str:
    return f"{start.year}/{str(end.year)[2:]}"

def read_cache(name: str) -> dict:
    cache = CACHE_DIR / name
    if not cache.exists():
        sys.exit(f"Falta _cache/{name}. La simulacion final se reproduce a partir "
                 "de los datos guardados en _cache/; no se descargan.")
    return json.loads(cache.read_text(encoding="utf-8"))

def read_climate(start: date, end: date) -> dict[date, ClimateData]:
    """Clima diario de una temporada, de la descarga de Open-Meteo de OPEN_METEO_DIR. El clima de
    los archivos {SECTOR_NAME}_{inicio}_{fin}.json no se usa; de ellos solo se lee el NDVI."""
    name = f"{OPEN_METEO_DIR}/{SECTOR_NAME}_clima_{start}_{end}.json"
    return {date.fromisoformat(k): ClimateData(**v) for k, v in read_cache(name)["climate"].items()}


def build_season(start: date, end: date) -> list[Day]:
    clim = read_climate(start, end)
    raw_ndvi = read_cache(f"{SECTOR_NAME}_{start}_{end}.json")["ndvi"]
    ndvi: dict[date, float] = {date.fromisoformat(k): nd for k, nd in raw_ndvi}
    image_dates = sorted(ndvi)

    days, d = [], start
    while d <= end:
        c = clim.get(d)
        if c is None:
            sys.exit(f"Falta el clima del {d} en _cache/; el balance diario no admite huecos.")
        image_date = select_image_date(image_dates, d)
        sat = (SatelliteData(sector_id=0, date=image_date, ndvi=ndvi[image_date], cloud_cover_pct=0.0)
               if image_date is not None else None)
        days.append(Day(
            date=d,
            eto_om_mm=c.eto_reference_mm,
            eto_pm_mm=calculate_eto(c, LAT, d).eto_mm, # Altitud estimada desde la presion
            eto_pm_rh_mm=calculate_eto(c.model_copy(update={"dew_point_c": None}), LAT, d).eto_mm,
            kc=calculate_kc(CROP, d, sat, HAIL_NET),
            precip_mm=c.precipitation_mm,
        ))
        d += timedelta(days=1)
    return days

def load_seasons() -> dict[str, list[Day]]:
    return {season_label(s, e): build_season(s, e) for s, e in SEASONS}

def monthly_climate(clim: dict[date, ClimateData]) -> dict[int, tuple[float, float]]:
    """ETo y precipitacion efectiva de cada mes (mm). La Pe se calcula dia por dia con la regla del sistema."""
    eto: dict[int, float] = defaultdict(float)
    pe: dict[int, float] = defaultdict(float)
    for d, c in clim.items():
        eto_mm = c.eto_reference_mm if c.eto_reference_mm is not None else calculate_eto(c, LAT, d).eto_mm
        eto[d.month] += eto_mm
        pe[d.month] += effective_precipitation(c.precipitation_mm, eto_mm)
    return {m: (eto[m], pe[m]) for m in eto}

def load_climate_series() -> dict[str, dict[int, tuple[float, float]]]:
    """ETo y precipitacion efectiva de cada mes de las temporadas de CLIMATE_SEASONS."""
    return {season_label(s, e): monthly_climate(read_climate(s, e)) for s, e in CLIMATE_SEASONS}

def planned_requirement(label: str, seasons: dict[str, list[Day]],
                        climate: dict[str, dict[int, tuple[float, float]]]) -> list[MonthRequirement]:
    """Requerimiento medio de cada mes para planificar la temporada 'label', sin datos de esa
    temporada: Kc medio de las otras temporadas del estudio; ETo y Pe medias de las otras
    temporadas de la serie climatica."""
    result = []
    for m in SEASON_MONTHS:
        kc = mean(x.kc.kc for other, days in seasons.items() if other != label
                  for x in days if x.date.month == m)
        others = [months[m] for other, months in climate.items() if other != label]
        result.append(MonthRequirement(m, kc, mean(e for e, _ in others), mean(p for _, p in others)))
    return result

def daily_requirement(days: list[Day], months: list[MonthRequirement]) -> list[float]:
    """Requerimiento de cada dia de la temporada: el de su mes repartido en partes iguales entre los dias del mes."""
    by_month = {r.month: r.requirement_mm for r in months}
    n_days = Counter(x.date.month for x in days)
    return [by_month[x.date.month] / n_days[x.date.month] for x in days]

def season_requirement(days: list[Day]) -> list[MonthRequirement]:
    """Requerimiento neto de cada mes con los datos de la temporada, con la misma formula que el
    requerimiento medio: max(0, Kc medio del mes x ETo del mes - precipitacion efectiva del mes),
    con el Kc medio como promedio del Kc diario."""
    result = []
    for m in SEASON_MONTHS:
        month = [x for x in days if x.date.month == m]
        kc = mean(x.kc.kc for x in month)
        eto = sum(x.eto_mm for x in month)
        pe = sum(effective_precipitation(x.precip_mm, x.eto_mm) for x in month)
        result.append(MonthRequirement(m, kc, eto, pe))
    return result

def daily_sum_requirement(days: list[Day]) -> dict[int, float]:
    """Requerimiento de cada mes sumado dia por dia: Sumatoria max(0, ETc - Pe). Es la formula
    de la simulacion exploratoria (sim_efficiency.py); descarta la lluvia que supera el
    consumo de cada dia, aunque el suelo la almacene."""
    return {m: sum(max(0.0, x.etc_mm - effective_precipitation(x.precip_mm, x.eto_mm))
                   for x in days if x.date.month == m) for m in SEASON_MONTHS}


def main() -> None:
    seasons = load_seasons()
    rows = []
    for label, days in seasons.items():
        om = [(x.eto_om_mm, x.eto_pm_mm) for x in days if x.eto_om_mm is not None]
        eto_om = sum(a for a, _ in om)
        eto_pm = sum(b for _, b in om)
        rows.append({
            "temporada": label,
            "dias": len(days),
            "dias_sin_eto_om": len(days) - len(om),
            "eto_om_mm": round(eto_om, 1),
            "eto_pm_mm": round(eto_pm, 1),
            "dif_pm_om_pct": round(100 * (eto_pm - eto_om) / eto_om, 2),
            "dias_kc_ndvi": sum(x.kc.source is KcSource.s2_dynamic for x in days),
            "etc_mm": round(sum(x.etc_mm for x in days), 1),
            "lluvia_mm": round(sum(x.precip_mm for x in days), 1),
        })
    print(f"Ubicacion: {SECTOR_FILE.name}")
    print(pd.DataFrame(rows).to_string(index=False))

    climate = load_climate_series()
    print("\nRequerimiento medio de cada mes del calendario planificado (mm)")
    req_rows = []
    for label, days in seasons.items():
        months = planned_requirement(label, seasons, climate)
        req_rows.append({
            "temporada": label,
            **{f"mes_{r.month}": round(r.requirement_mm, 1) for r in months},
            "total": round(sum(r.requirement_mm for r in months), 1),
            "suma_diaria": round(sum(daily_requirement(days, months)), 1),
        })
    print(pd.DataFrame(req_rows).to_string(index=False))
    print("\nRequerimiento de cada mes con los datos de cada temporada (mm)")
    own_rows = []
    for label, days in seasons.items():
        months = season_requirement(days)
        own_rows.append({
            "temporada": label,
            **{f"mes_{r.month}": round(r.requirement_mm, 1) for r in months},
            "total": round(sum(r.requirement_mm for r in months), 1),
            "suma_dia_por_dia": round(sum(daily_sum_requirement(days).values()), 1),
        })
    print(pd.DataFrame(own_rows).to_string(index=False))

if __name__ == "__main__":
    main()