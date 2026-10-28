"""
Verificación de los datos climáticos de la simulación final (sección 11 del
protocolo y corrección (c) de la sección 13).

Verificación de la ETo. Cada comparación se hace día por día, en las tres
temporadas del estudio:
- ETo propia (Penman-Monteith) frente a la de Open-Meteo, en el sector, con la
  presión de vapor real desde el punto de rocío [Ec. 14] y desde la humedad
  relativa media [Ec. 19]. La propia y la de Open-Meteo se calculan con los mismos
  datos climáticos, por lo que la comparación verifica la implementación del
  cálculo, no su exactitud.
- ETo de Open-Meteo, en las coordenadas de la estación San Rafael Aero (SMN, OMM
  87509), frente a la ETo calculada con los datos de esa estación: observaciones
  horarias de NOAA ISD-Lite agregadas por día local (UTC-3), solo los días con al
  menos MIN_HOURLY_OBS observaciones; radiación de Hargreaves (la estación no la
  mide) y presión según la altitud.
- Control: ETo de Open-Meteo, en las coordenadas de la estación del INTA en Rama
  Caída, frente a la ETo calculada con su temperatura y su punto de rocío y el
  viento de San Rafael Aero, porque esa estación no mide viento.
La ETo de las estaciones se calcula con calculate_eto, la misma función del sistema.

Caracterización climática. ETo, lluvia y precipitación efectiva de septiembre a
abril de cada temporada del estudio según ERA5, frente a las temporadas 1991/92 a
2019/20 de ERA5 (serie 1991-2020): diferencia con la media y percentil. Es el mismo
modelo de los dos lados. Se informan también los totales según IFS (Open-Meteo
best_match), que son los datos que usa el sistema.

Lluvia frente a las estaciones, solo como diagnóstico: no va a los resultados de la
simulación (_out/); el motivo está en el README. Lluvia de septiembre a abril de las
temporadas 2017/18 a 2023/24 de cada estación en sus días con dato, frente a la de
IFS y ERA5 en el sector sumada en esos mismos días:
- San Rafael Aero: lluvia diaria del GSOD de NOAA (día UTC). Un día tiene dato si su
  total cubre las 24 h (marcas D, F y G). Como sensibilidad, también con todos los
  días con algún informe (todas las marcas menos I, que es sin informe). Los días con
  el valor faltante del GSOD (99.99) no están en los datos guardados. Una marca de
  24 h no garantiza que la ventana de la estación coincida con el día de IFS y ERA5,
  que es el día local (UTC-3).
- Rama Caída: lluvia pluviométrica y cronológica del SIGA del INTA, los días con valor.
Con pocos días con dato, la suma vale para esos días, no para la temporada completa.
Los días de GSOD_SUSPECT_DAYS no se excluyen; se informan aparte.

Diagnóstico (desde backend/):  venv/Scripts/python.exe -m evaluation.final.climate_check
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import date
from statistics import correlation, linear_regression, mean

import pandas as pd

from app.calculation.eto import _extraterrestrial_radiation, _saturation_vapor_pressure, calculate_eto
from app.calculation.water_balance import effective_precipitation
from app.schemas.climate import ClimateData

from .data import CLIMATE_SEASONS, OPEN_METEO_DIR, SEASONS, Day, load_seasons, read_cache, read_climate, season_label

ALL_SEASONS = "todas" # rotulo de los resultados con las temporadas juntas
OWN_DEW_POINT_VS_OPEN_METEO = "ETo propia Ec. 14 (punto de rocio) vs Open-Meteo (sector)"
OWN_HUMIDITY_VS_OPEN_METEO = "ETo propia Ec. 19 (humedad relativa media) vs Open-Meteo (sector)"
OPEN_METEO_VS_STATION = "Open-Meteo vs San Rafael Aero"
OPEN_METEO_VS_CONTROL = "Open-Meteo vs Rama Caida (control)"

MIN_HOURLY_OBS = 20 # observaciones horarias minimas de cada variable para usar un dia de la estacion
KRS = 0.16 # coeficiente de la radiacion de Hargreaves para zonas del interior (Allen et al., 1998, Ec. 50)

# Serie de referencia de la caracterizacion climatica: temporadas 1991/92 a 2019/20 (1 de septiembre al 30 de abril)
REFERENCE_SEASONS = [(date(y, 9, 1), date(y + 1, 4, 30)) for y in range(1991, 2020)]
ETO = "ETo"
RAIN = "lluvia"
EFFECTIVE_RAIN = "precipitacion efectiva"

SAN_RAFAEL_AERO = "San Rafael Aero"
RAMA_CAIDA = "Rama Caida"
# Marcas de la lluvia diaria del GSOD: D, F y G cubren las 24 h; A, B, C y E son informes parciales;
# H es un 0 informado con lluvia en las observaciones horarias; I es sin informe (el GSOD pone 0)
GSOD_COMPLETE = "24 h completas (D, F, G)"
GSOD_REPORTED = "con algun informe (todas menos I)"
GSOD_FLAGS = {GSOD_COMPLETE: {"D", "F", "G"}, GSOD_REPORTED: {"A", "B", "C", "D", "E", "F", "G", "H"}}
RAMA_CAIDA_COLUMNS = {"pluviometrica": "lluvia_pluviometrica", "cronologica": "lluvia_cronologica"}
# Dias de San Rafael Aero con lluvia muy por encima de IFS, ERA5 y Rama Caida: no se excluyen, se informan aparte
GSOD_SUSPECT_DAYS = [date(2020, 11, 10), date(2020, 12, 18), date(2021, 4, 8)]

@dataclass(frozen=True)
class EtoCheck:
    """ETo estimada frente a una ETo de referencia, dia por dia."""
    comparison: str # OWN_DEW_POINT_VS_OPEN_METEO, OWN_HUMIDITY_VS_OPEN_METEO, OPEN_METEO_VS_STATION u OPEN_METEO_VS_CONTROL
    period: str # temporada, o ALL_SEASONS
    n_days: int # dias comparados
    reference_mm: float # ETo de referencia media diaria
    estimate_mm: float # ETo estimada media diaria
    mean_diff_mm: float # media de (estimada - referencia)
    rmse_mm: float # error cuadratico medio
    a: float # ordenada al origen de la regresion estimada = a + b * referencia
    b: float # pendiente de esa regresion
    r2: float # coeficiente de determinacion de esa regresion
    b0: float # pendiente de la regresion por el origen: estimada = b0 * referencia (Ippolito et al., 2024)

Pairs = list[tuple[float, float]] # (referencia, estimada) de cada dia

def eto_check(comparison: str, period: str, pairs: Pairs) -> EtoCheck:
    reference = [r for r, _ in pairs]
    estimate = [e for _, e in pairs]
    diffs = [e - r for r, e in pairs]
    fit = linear_regression(reference, estimate)
    return EtoCheck(
        comparison=comparison,
        period=period,
        n_days=len(pairs),
        reference_mm=mean(reference),
        estimate_mm=mean(estimate),
        mean_diff_mm=mean(diffs),
        rmse_mm=math.sqrt(mean(d * d for d in diffs)),
        a=fit.intercept,
        b=fit.slope,
        r2=correlation(reference, estimate) ** 2,
        b0=linear_regression(reference, estimate, proportional=True).slope,
    )

def eto_checks(comparison: str, pairs: dict[str, Pairs]) -> list[EtoCheck]:
    """Comparacion por temporada y con las temporadas juntas."""
    rows = [eto_check(comparison, label, p) for label, p in pairs.items()]
    rows.append(eto_check(comparison, ALL_SEASONS, [x for p in pairs.values() for x in p]))
    return rows

def own_pairs(seasons: dict[str, list[Day]], from_humidity: bool) -> dict[str, Pairs]:
    """ETo de Open-Meteo (referencia) y propia (estimada) en el sector, con ea desde el punto de rocio
    [Ec. 14] o, con from_humidity, desde la humedad relativa media [Ec. 19]."""
    return {label: [(x.eto_om_mm, x.eto_pm_rh_mm if from_humidity else x.eto_pm_mm) for x in days
                    if x.eto_om_mm is not None]
            for label, days in seasons.items()}

def pressure_from_elevation(elevation_m: float) -> float:
    """Presion atmosferica (kPa) segun la altitud [Ec. 7]."""
    return 101.3 * ((293 - 0.0065 * elevation_m) / 293) ** 5.26

def station_eto(d: date, lat: float, elevation_m: float, tmax: float, tmin: float, tmean: float,
                ea: float, u10: float) -> float:
    """ETo con datos de estacion, con calculate_eto. Radiacion de Hargreaves [Ec. 50] y presion
    segun la altitud. La humedad relativa es la que da la presion de vapor real ea [Ec. 19]."""
    es = (_saturation_vapor_pressure(tmax) + _saturation_vapor_pressure(tmin)) / 2
    ra = _extraterrestrial_radiation(math.radians(lat), d.timetuple().tm_yday)
    climate = ClimateData(
        date=d, temp_max_c=tmax, temp_min_c=tmin, temp_mean_c=tmean, humidity_pct=100 * ea / es,
        wind_speed_10m=u10, solar_radiation_mj=KRS * math.sqrt(max(tmax - tmin, 0.0)) * ra,
        precipitation_mm=0.0, pressure_kpa=pressure_from_elevation(elevation_m),
    )
    return calculate_eto(climate, lat, d, elevation_m).eto_mm

def open_meteo_eto(name: str) -> dict[date, float]:
    """ETo de Open-Meteo en las coordenadas de una estacion."""
    daily = read_cache(f"{OPEN_METEO_DIR}/OpenMeteo_{name}_2021-09-01_2024-04-30.json")["daily"]
    return {date.fromisoformat(t): e for t, e in zip(daily["time"], daily["et0_fao_evapotranspiration"])
            if e is not None}

def by_season(rows: list[tuple[date, float, float]]) -> dict[str, Pairs]:
    """Agrupa (dia, referencia, estimada) por temporada del estudio; descarta los dias fuera de ellas."""
    result: dict[str, Pairs] = {season_label(s, e): [] for s, e in SEASONS}
    for d, reference, estimate in rows:
        for s, e in SEASONS:
            if s <= d <= e:
                result[season_label(s, e)].append((reference, estimate))
    return result

def station_pairs() -> tuple[dict[str, Pairs], dict[str, Pairs]]:
    """ETo de la estacion (referencia) y de Open-Meteo en sus coordenadas (estimada): San Rafael
    Aero y el control de Rama Caida."""
    airport = read_cache("SanRafaelAero_diario_2017-09-01_2024-04-30.json")
    st = airport["estacion"]
    airport_days = {date.fromisoformat(k): v for k, v in airport["isd_dia_local"].items()}
    om = open_meteo_eto("SanRafaelAero")
    station: list[tuple[date, float, float]] = []
    for d, v in airport_days.items():
        if d in om and min(v["n_obs"], v["n_rocio"], v["n_viento"]) >= MIN_HOURLY_OBS:
            eto = station_eto(d, st["latitud"], st["elevacion_m"], v["tmax"], v["tmin"], v["tmean"],
                              v["ea"], v["u10"])
            station.append((d, eto, om[d]))

    rama = read_cache("RamaCaida_diario_2017-09-01_2024-04-30.json")
    rc = rama["estacion"]
    om = open_meteo_eto("RamaCaida")
    control: list[tuple[date, float, float]] = []
    for k, v in rama["diario"].items():
        d = date.fromisoformat(k)
        wind = airport_days.get(d)
        if (d in om and wind is not None and wind["n_viento"] >= MIN_HOURLY_OBS
                and all(v[x] is not None for x in ("tmax", "tmin", "tmean", "tdew"))):
            eto = station_eto(d, rc["latitud"], rc["altura_m"], v["tmax"], v["tmin"], v["tmean"],
                              _saturation_vapor_pressure(v["tdew"]), wind["u10"]) # Ec. 14
            control.append((d, eto, om[d]))
    return by_season(station), by_season(control)

def verify_eto(seasons: dict[str, list[Day]]) -> list[EtoCheck]:
    station, control = station_pairs()
    return (eto_checks(OWN_DEW_POINT_VS_OPEN_METEO, own_pairs(seasons, from_humidity=False))
            + eto_checks(OWN_HUMIDITY_VS_OPEN_METEO, own_pairs(seasons, from_humidity=True))
            + eto_checks(OPEN_METEO_VS_STATION, station)
            + eto_checks(OPEN_METEO_VS_CONTROL, control))
@dataclass(frozen=True)
class SeasonClimate:
    """Total de septiembre a abril de una temporada del estudio frente a la serie de referencia."""
    period: str # temporada
    variable: str # ETO, RAIN o EFFECTIVE_RAIN
    era5_mm: float # total de la temporada segun ERA5
    reference_mean_mm: float # media de la serie de referencia (ERA5)
    reference_min_mm: float # menor total de la serie de referencia
    reference_max_mm: float # mayor total de la serie de referencia
    diff_mm: float # era5_mm - reference_mean_mm
    diff_pct: float # en % de la media de referencia
    percentile: float # % de temporadas de referencia con un total menor; los empates cuentan la mitad
    ifs_mm: float # total de la temporada segun IFS (los datos del sistema)

def read_era5() -> dict[date, tuple[float, float]]:
    """ETo y lluvia diarias de ERA5 en el sector."""
    raw = read_cache(f"{OPEN_METEO_DIR}/Malbec_era5_1991-01-01_2024-04-30.json")["daily"]
    return {date.fromisoformat(d): (e, p)
            for d, e, p in zip(raw["date"], raw["eto_reference_mm"], raw["precipitation_mm"])}

def season_totals(daily: dict[date, tuple[float, float]], start: date, end: date) -> dict[str, float]:
    """ETo, lluvia y precipitacion efectiva totales entre start y end. daily: (ETo, lluvia) de cada dia.
    La precipitacion efectiva se calcula dia por dia con la regla del sistema."""
    days = [v for d, v in daily.items() if start <= d <= end]
    return {
        ETO: sum(e for e, _ in days),
        RAIN: sum(p for _, p in days),
        EFFECTIVE_RAIN: sum(effective_precipitation(p, e) for e, p in days),
    }

def percentile(value: float, reference: list[float]) -> float:
    """% de los valores de referencia menores que value; los iguales cuentan la mitad."""
    below = sum(r < value for r in reference)
    ties = sum(r == value for r in reference)
    return 100 * (below + 0.5 * ties) / len(reference)

def characterize(seasons: dict[str, list[Day]]) -> list[SeasonClimate]:
    era5 = read_era5()
    ifs = {x.date: (x.eto_mm, x.precip_mm) for days in seasons.values() for x in days}
    reference = [season_totals(era5, s, e) for s, e in REFERENCE_SEASONS]
    rows: list[SeasonClimate] = []
    for s, e in SEASONS:
        season_era5 = season_totals(era5, s, e)
        season_ifs = season_totals(ifs, s, e)
        for variable in (ETO, RAIN, EFFECTIVE_RAIN):
            values = [r[variable] for r in reference]
            ref_mean = mean(values)
            total = season_era5[variable]
            rows.append(SeasonClimate(
                period=season_label(s, e),
                variable=variable,
                era5_mm=total,
                reference_mean_mm=ref_mean,
                reference_min_mm=min(values),
                reference_max_mm=max(values),
                diff_mm=total - ref_mean,
                diff_pct=100 * (total - ref_mean) / ref_mean,
                percentile=percentile(total, values),
                ifs_mm=season_ifs[variable],
            ))
    return rows

@dataclass(frozen=True)
class StationRain:
    """Lluvia de una estacion en sus dias con dato de una temporada, y la de IFS y ERA5 en el sector
    sumada en esos mismos dias."""
    station: str # SAN_RAFAEL_AERO o RAMA_CAIDA
    data: str # dias con dato: criterio de GSOD_FLAGS (San Rafael Aero) o columna de lluvia (Rama Caida)
    period: str # temporada
    n_days: int # dias con dato
    season_days: int # dias de la temporada
    station_mm: float # lluvia de la estacion
    ifs_mm: float # lluvia de IFS (los datos del sistema)
    era5_mm: float # lluvia de ERA5

RainSeries = dict[date, float] # lluvia de cada dia con dato

def station_rain_series() -> dict[tuple[str, str], RainSeries]:
    """Lluvia diaria de cada estacion en sus dias con dato, por (estacion, dias con dato)."""
    gsod = read_cache("SanRafaelAero_diario_2017-09-01_2024-04-30.json")["gsod_lluvia_dia_utc"]
    rama = read_cache("RamaCaida_diario_2017-09-01_2024-04-30.json")["diario"]
    series: dict[tuple[str, str], RainSeries] = {}
    for rule, flags in GSOD_FLAGS.items():
        series[(SAN_RAFAEL_AERO, rule)] = {date.fromisoformat(k): v["mm"] for k, v in gsod.items()
                                           if v["marca"] in flags}
    for label, column in RAMA_CAIDA_COLUMNS.items():
        series[(RAMA_CAIDA, label)] = {date.fromisoformat(k): v[column] for k, v in rama.items()
                                       if v[column] is not None}
    return series

def sector_rain() -> tuple[RainSeries, RainSeries]:
    """Lluvia diaria de IFS (los datos del sistema) y de ERA5 en el sector."""
    ifs = {d: c.precipitation_mm for s, e in CLIMATE_SEASONS for d, c in read_climate(s, e).items()}
    era5 = {d: p for d, (_, p) in read_era5().items()}
    return ifs, era5

def station_rain(station: str, data: str, series: RainSeries, start: date, end: date,
                 ifs: RainSeries, era5: RainSeries) -> StationRain:
    days = [d for d in series if start <= d <= end]
    return StationRain(
        station=station,
        data=data,
        period=season_label(start, end),
        n_days=len(days),
        season_days=(end - start).days + 1,
        station_mm=sum(series[d] for d in days),
        ifs_mm=sum(ifs[d] for d in days),
        era5_mm=sum(era5[d] for d in days),
    )

def compare_rain() -> list[StationRain]:
    ifs, era5 = sector_rain()
    return [station_rain(station, data, series, s, e, ifs, era5)
            for (station, data), series in station_rain_series().items() for s, e in CLIMATE_SEASONS]

@dataclass(frozen=True)
class SuspectDay:
    """Dia de GSOD_SUSPECT_DAYS: lluvia de San Rafael Aero frente a IFS, ERA5 y Rama Caida."""
    date: date
    flag: str # marca del GSOD
    station_mm: float # lluvia de San Rafael Aero
    ifs_mm: float
    era5_mm: float
    rama_caida_pluviometrica_mm: float | None
    rama_caida_cronologica_mm: float | None

def suspect_days() -> list[SuspectDay]:
    gsod = read_cache("SanRafaelAero_diario_2017-09-01_2024-04-30.json")["gsod_lluvia_dia_utc"]
    rama = read_cache("RamaCaida_diario_2017-09-01_2024-04-30.json")["diario"]
    ifs, era5 = sector_rain()
    rows: list[SuspectDay] = []
    for d in GSOD_SUSPECT_DAYS:
        station, rc = gsod[str(d)], rama.get(str(d), {})
        rows.append(SuspectDay(
            date=d,
            flag=station["marca"],
            station_mm=station["mm"],
            ifs_mm=ifs[d],
            era5_mm=era5[d],
            rama_caida_pluviometrica_mm=rc.get("lluvia_pluviometrica"),
            rama_caida_cronologica_mm=rc.get("lluvia_cronologica"),
        ))
    return rows

def without_suspect_days() -> list[StationRain]:
    """San Rafael Aero en las temporadas con dias de GSOD_SUSPECT_DAYS, sin esos dias. Es informacion
    aparte, no un resultado."""
    ifs, era5 = sector_rain()
    rows: list[StationRain] = []
    for (station, data), series in station_rain_series().items():
        if station != SAN_RAFAEL_AERO:
            continue
        kept = {d: v for d, v in series.items() if d not in GSOD_SUSPECT_DAYS}
        rows += [station_rain(station, data, kept, s, e, ifs, era5) for s, e in CLIMATE_SEASONS
                 if any(s <= d <= e for d in GSOD_SUSPECT_DAYS)]
    return rows


def main() -> None:
    seasons = load_seasons()
    print("Verificacion de la ETo (mm/dia)")
    print(pd.DataFrame([asdict(r) for r in verify_eto(seasons)]).round(3).to_string(index=False))
    print(f"\nCaracterizacion climatica, 1/9 a 30/4 (mm). Referencia: ERA5 {len(REFERENCE_SEASONS)} temporadas "
          f"({season_label(*REFERENCE_SEASONS[0])} a {season_label(*REFERENCE_SEASONS[-1])})")
    print(pd.DataFrame([asdict(r) for r in characterize(seasons)]).round(1).to_string(index=False))

    rain = pd.DataFrame([asdict(r) for r in compare_rain()]).round(1)
    sensitivity = rain["data"] == GSOD_REPORTED
    print("\nLluvia frente a las estaciones, 1/9 a 30/4 (mm), en los dias con dato de cada estacion")
    print(rain[~sensitivity].to_string(index=False))
    print(f"\nSensibilidad: San Rafael Aero con los dias {GSOD_REPORTED}")
    print(rain[sensitivity].to_string(index=False))
    print("\nInformacion aparte: dias de San Rafael Aero con lluvia muy por encima de IFS, ERA5 y Rama Caida "
          "(no se excluyen de las tablas anteriores)")
    print(pd.DataFrame([asdict(r) for r in suspect_days()]).round(1).to_string(index=False))
    print("Las mismas temporadas sin esos dias:")
    print(pd.DataFrame([asdict(r) for r in without_suspect_days()]).round(1).to_string(index=False))

if __name__ == "__main__":
    main()
