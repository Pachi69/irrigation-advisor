"""Servicio de la seccion DEMO.

Corre el pipeline de recomendacion sobre una fecha de verano preset, en memoria,
reutilizando las funciones PURAS del motor (calculate_kc, calculate_water_balance,
calculate_urgency) + los clientes de ingesta (GEE, Open-Meteo). No toca la base
de datos ni el pipeline real.

Cachea el resultado (snapshot JSON + thumbnail PNG) en disco (app/demo/cache/),
para que la demo en vivo no dependa de GEE/red en el peor momento. La primera
llamada calcula y persiste; las siguientes leen del cache (salvo force=True).
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

from app.demo.fixtures import (
    DEMO_ANCHOR_DATE,
    DEMO_SECTOR,
    DEMO_TARGET_DATE,
    DemoSector,
)
from app.schemas.calculation import EToResult
from app.schemas.climate import ForecastDay
from app.schemas.demo import DemoSnapshot, DemoTrajectoryPoint
from app.schemas.satellite import SatelliteData
from app.ingestion.climate import get_climate_data_for_range
from app.ingestion.satellite import (
    SatelliteIndices,
    get_satellite_indices,
    get_satellite_indices_for_range,
)
from app.calculation.eto import calculate_eto
from app.calculation.kc import calculate_kc
from app.calculation.water_balance import calculate_water_balance
from app.calculation.urgency import calculate_urgency
from app.calculation.crop_params import get_root_depth, get_depletion_factor
from app.calculation.irrigation import efficiency_for, mm_to_time_min, mm_to_volume_m3

logger = logging.getLogger(__name__)

# Igual que el servicio satelital real (services/satellite.py)
NDVI_MAX_AGE_DAYS = 15
FORECAST_DAYS = 3

_CACHE_DIR = Path(__file__).resolve().parents[1] / "demo" / "cache"
_SNAPSHOT_FILE = _CACHE_DIR / "snapshot.json"
_THUMBNAIL_FILE = _CACHE_DIR / "target.png"

# Cache en memoria (ademas del de disco, para evitar releer en cada request)
_snapshot_mem: DemoSnapshot | None = None


def _ndvi_for_day(
    day: date,
    sorted_dates: list[date],
    s2_by_date: dict[date, SatelliteIndices],
) -> tuple[SatelliteData | None, date | None]:
    """NDVI vigente para un dia: imagen mas reciente con fecha <= day dentro de
    NDVI_MAX_AGE_DAYS (carry-forward), mismo criterio que el pipeline real."""
    chosen: date | None = None
    for d in sorted_dates:
        if d <= day:
            chosen = d
        else:
            break
    if chosen is None or (day - chosen).days > NDVI_MAX_AGE_DAYS:
        return None, None
    idx = s2_by_date[chosen]
    return (
        SatelliteData(sector_id=0, date=chosen, ndvi=idx.ndvi, cloud_cover_pct=idx.cloud_cover_pct),
        chosen,
    )


def _eto_for(climate, sector: DemoSector, day: date) -> EToResult:
    """ETo del dia: usa el et0 del archivo; si falta, lo calcula (FAO-56 PM)."""
    if climate.eto_reference_mm is not None:
        return EToResult(eto_mm=climate.eto_reference_mm)
    return calculate_eto(climate, sector.latitude, day, sector.elevation_m)


def _fetch_demo_thumbnail(sector: DemoSector, target: date) -> bytes | None:
    """Pide a GEE el thumbnail NDVI de la imagen limpia mas reciente <= target."""
    try:
        indices = get_satellite_indices(sector.polygon_geojson, target)
    except RuntimeError as e:
        logger.warning("Demo: no se pudo traer el thumbnail S2: %s", e)
        return None
    if indices is None:
        return None
    return indices.thumbnail_png


def _compute() -> DemoSnapshot:
    """Corre el pipeline completo sobre el caso demo y arma el snapshot."""
    sector = DEMO_SECTOR
    anchor, target = DEMO_ANCHOR_DATE, DEMO_TARGET_DATE
    root_depth = get_root_depth(sector.crop_type)
    p = get_depletion_factor(sector.crop_type)

    # 1) Clima real ancla..objetivo+3 (los 3 dias siguientes = "pronostico perfecto")
    climate_end = target + timedelta(days=FORECAST_DAYS)
    climate_by_date = get_climate_data_for_range(
        sector.latitude, sector.longitude, anchor, climate_end
    )

    # 2) Imagenes S2 reales (NDVI), con lookback para el carry-forward del primer dia
    s2_list = get_satellite_indices_for_range(
        sector.polygon_geojson,
        anchor - timedelta(days=NDVI_MAX_AGE_DAYS),
        target,
    )
    s2_by_date = {idx.image_date: idx for idx in s2_list}
    sorted_dates = sorted(s2_by_date)

    # 3) Roll dia por dia desde el ancla (seed 0: la lluvia ancla lo re-satura igual)
    previous_deficit = 0.0
    trajectory: list[DemoTrajectoryPoint] = []
    last: dict = {}

    current = anchor
    while current <= target:
        climate = climate_by_date.get(current)
        if climate is None:
            logger.warning("Demo: sin clima para %s; dia omitido", current)
            current += timedelta(days=1)
            continue

        sat_data, ndvi_date = _ndvi_for_day(current, sorted_dates, s2_by_date)
        eto = _eto_for(climate, sector, current)
        kc_result = calculate_kc(sector.crop_type, current, sat_data, sector.hail_net_type)
        balance = calculate_water_balance(
            eto=eto,
            kc=kc_result,
            precipitation_mm=climate.precipitation_mm,
            previous_deficit_mm=previous_deficit,
            soil_type=sector.soil_type,
            root_depth_m=root_depth,
            depletion_factor_p=p,
            irrigation_mm=0.0,
        )
        etc_mm = eto.eto_mm * kc_result.kc

        trajectory.append(DemoTrajectoryPoint(
            date=current,
            deficit_mm=round(balance.water_deficit_mm, 1),
            deficit_pct=round(min(100.0, balance.water_deficit_mm / balance.taw_mm * 100), 1)
            if balance.taw_mm else 0.0,
            etc_mm=round(etc_mm, 2),
            precipitation_mm=round(climate.precipitation_mm, 1),
            kc=round(kc_result.kc, 3),
            kc_source=kc_result.source,
            ndvi=round(sat_data.ndvi, 4) if sat_data and sat_data.ndvi is not None else None,
        ))
        last = {
            "climate": climate, "eto": eto, "kc": kc_result,
            "balance": balance, "sat": sat_data, "ndvi_date": ndvi_date, "etc": etc_mm,
        }
        previous_deficit = balance.water_deficit_mm
        current += timedelta(days=1)

    if not last:
        raise RuntimeError("No se pudo construir el balance del caso demo (sin clima en el rango).")

    # 4) Pronostico perfecto: clima real de target+1..+3 con probabilidad 100%
    forecast: list[ForecastDay] = []
    for i in range(1, FORECAST_DAYS + 1):
        c = climate_by_date.get(target + timedelta(days=i))
        if c is None:
            continue
        forecast.append(ForecastDay(
            date=c.date,
            temp_max_c=c.temp_max_c,
            temp_min_c=c.temp_min_c,
            precipitation_mm=c.precipitation_mm,
            precipitation_probability_pct=100.0,
            eto_reference_mm=c.eto_reference_mm if c.eto_reference_mm is not None
            else _eto_for(c, sector, c.date).eto_mm,
        ))

    # 5) Urgencia en el dia objetivo
    urgency = calculate_urgency(last["balance"], forecast, last["kc"])

    # 6) Equivalencias operativas
    eff = efficiency_for(sector.irrigation_type)
    mm = urgency.recommended_irrigation_mm
    volume_m3 = mm_to_volume_m3(round(mm), sector.area_ha, eff)
    time_min = mm_to_time_min(mm, sector.flow_rate_ls_ha, eff)

    # 7) Estado ACTUAL (reposo invernal) del mismo sector -> contraste
    current_kc = calculate_kc(sector.crop_type, date.today(), None, sector.hail_net_type)

    bal, sat = last["balance"], last["sat"]
    snapshot = DemoSnapshot(
        sector_name=sector.name,
        crop_type=sector.crop_type.value,
        variety=sector.variety,
        area_ha=sector.area_ha,
        polygon_geojson=sector.polygon_geojson,
        anchor_date=anchor,
        target_date=target,
        urgency_level=urgency.urgency_level,
        recommended_irrigation_mm=mm,
        volume_m3=round(volume_m3, 1) if volume_m3 is not None else None,
        time_min=round(time_min, 1) if time_min is not None else None,
        reason=urgency.reason,
        confidence=urgency.confidence,
        water_deficit_mm=round(bal.water_deficit_mm, 1),
        ks=round(bal.ks, 2),
        taw_mm=round(bal.taw_mm, 1),
        raw_mm=round(bal.raw_mm, 1),
        eto_mm=round(last["eto"].eto_mm, 2),
        etc_mm=round(last["etc"], 2),
        kc=round(last["kc"].kc, 3),
        kc_source=last["kc"].source,
        phenological_stage=last["kc"].phenological_stage,
        ndvi=round(sat.ndvi, 4) if sat and sat.ndvi is not None else None,
        ndvi_date=last["ndvi_date"],
        cloud_cover_pct=round(sat.cloud_cover_pct, 1) if sat and sat.cloud_cover_pct is not None else None,
        current_kc=round(current_kc.kc, 3),
        current_kc_source=current_kc.source,
        current_phenological_stage=current_kc.phenological_stage,
        trajectory=trajectory,
        note=(
            "Balance anclado a la ultima lluvia significativa "
            f"({anchor.strftime('%d/%m')}-09/01/2026, ~51 mm) y rodado sin riegos "
            "cargados. Ilustra el mecanismo del sistema en plena temporada con NDVI "
            "satelital activo; no es el estado real exacto del lote."
        ),
    )
    return snapshot


def _write_cache(snapshot: DemoSnapshot, thumbnail: bytes | None) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _SNAPSHOT_FILE.write_text(snapshot.model_dump_json(), encoding="utf-8")
    if thumbnail is not None:
        _THUMBNAIL_FILE.write_bytes(thumbnail)


def _read_cached_snapshot() -> DemoSnapshot | None:
    if not _SNAPSHOT_FILE.exists():
        return None
    try:
        return DemoSnapshot.model_validate_json(_SNAPSHOT_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("Demo: cache de snapshot invalido (%s); se recalcula.", e)
        return None


def compute_demo_snapshot(force: bool = False) -> DemoSnapshot:
    """Devuelve el snapshot del caso demo (memoria -> disco -> calculo)."""
    global _snapshot_mem

    if not force:
        if _snapshot_mem is not None:
            return _snapshot_mem
        cached = _read_cached_snapshot()
        if cached is not None:
            _snapshot_mem = cached
            return cached

    logger.info("Demo: calculando snapshot (GEE + Open-Meteo)...")
    snapshot = _compute()
    thumbnail = _fetch_demo_thumbnail(DEMO_SECTOR, DEMO_TARGET_DATE)
    _write_cache(snapshot, thumbnail)
    _snapshot_mem = snapshot
    logger.info(
        "Demo: snapshot listo (deficit %.1f mm, urgencia %s, Kc %.3f %s)",
        snapshot.water_deficit_mm, snapshot.urgency_level.value,
        snapshot.kc, snapshot.kc_source.value,
    )
    return snapshot


def get_demo_thumbnail() -> bytes | None:
    """Devuelve el PNG del thumbnail NDVI del dia objetivo (lo calcula si falta)."""
    if not _THUMBNAIL_FILE.exists():
        compute_demo_snapshot()
    if _THUMBNAIL_FILE.exists():
        return _THUMBNAIL_FILE.read_bytes()
    return None