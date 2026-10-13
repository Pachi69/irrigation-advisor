"""Servicio de datos satelitales: busqueda y persistencia de imagenes S2."""
from bisect import bisect_right
from collections.abc import Sequence
from datetime import date as DateType, timedelta

import logging

from sqlalchemy.orm import Session

from app.models.sector import Sector as SectorModel
from app.models.satellite_record import SatelliteRecord
from app.schemas.satellite import SatelliteData
from app.ingestion.satellite import get_satellite_indices, get_satellite_indices_for_range

logger = logging.getLogger(__name__)

NDVI_MAX_AGE_DAYS = 15 # ventana hacia atras del prefetch de imagenes S2
SAT_FORWARD_FILL_MAX_DAYS = 5 # tope para el forward-fill del hueco inicial

def select_image_date(image_dates: Sequence[DateType], day: DateType) -> DateType | None:
    """Fecha de la imagen vigente para un dia (image_dates en orden ascendente).

      - Carry-forward: la imagen mas reciente con fecha <= dia, sin limite de antiguedad.
      - Hueco inicial: si no hay imagen previa, la primera imagen si esta dentro de
        SAT_FORWARD_FILL_MAX_DAYS (5) dias; si no, None (Kc tabular).
    """
    i = bisect_right(image_dates, day)
    if i > 0:
        return image_dates[i - 1]
    if image_dates and (image_dates[0] - day).days <= SAT_FORWARD_FILL_MAX_DAYS:
        return image_dates[0]
    return None

def _as_satellite_data(sector: SectorModel, record: SatelliteRecord) -> tuple[SatelliteData, DateType]:
    return (
        SatelliteData(
            sector_id=sector.id, date=record.date,
            ndvi=record.ndvi, cloud_cover_pct=record.cloud_cover_pct,
        ),
        record.date,
    )

def get_satellite_data_for_date(
    sector: SectorModel, target_date: DateType, db: Session
) -> tuple[SatelliteData | None, DateType | None]:
    """Devuelve el NDVI vigente a una fecha, con la regla de select_image_date."""
    previous = (
        db.query(SatelliteRecord)
        .filter(
            SatelliteRecord.sector_id == sector.id,
            SatelliteRecord.date <= target_date,
        )
        .order_by(SatelliteRecord.date.desc())
        .first()
    )
    following: SatelliteRecord | None = None
    if previous is None:
        following = (
            db.query(SatelliteRecord)
            .filter(
                SatelliteRecord.sector_id == sector.id,
                SatelliteRecord.date > target_date,
            )
            .order_by(SatelliteRecord.date.asc())
            .first()
        )
    records = {r.date: r for r in (previous, following) if r is not None}
    chosen_date = select_image_date(sorted(records), target_date)
    if chosen_date is None:
        return None, None
    return _as_satellite_data(sector, records[chosen_date])


def get_satellite_data_for_range(
    sector: SectorModel, start_date: DateType, end_date: DateType, db: Session
) -> dict[DateType, tuple[SatelliteData | None, DateType | None]]:
    """Resuelve el dato satelital vigente para cada dia de un rango, en memoria,
    con la regla de select_image_date.

    Returns:
        dict {fecha: (SatelliteData | None, fecha_imagen | None)} con una
        entrada por cada dia del rango.
    """
    # Ultima imagen anterior al rango: el carry-forward no tiene limite de antiguedad.
    previous = (
        db.query(SatelliteRecord)
        .filter(
            SatelliteRecord.sector_id == sector.id,
            SatelliteRecord.date < start_date,
        )
        .order_by(SatelliteRecord.date.desc())
        .first()
    )
    # Imagenes del rango, mas los dias de forward-fill posteriores al ultimo dia.
    forward_end = end_date + timedelta(days=SAT_FORWARD_FILL_MAX_DAYS)
    in_range = (
        db.query(SatelliteRecord)
        .filter(
            SatelliteRecord.sector_id == sector.id,
            SatelliteRecord.date >= start_date,
            SatelliteRecord.date <= forward_end,
        )
        .order_by(SatelliteRecord.date.asc())
        .all()
    )
    records = {r.date: r for r in in_range}
    if previous is not None:
        records[previous.date] = previous
    image_dates = sorted(records)

    result: dict[DateType, tuple[SatelliteData | None, DateType | None]] = {}
    current = start_date
    while current <= end_date:
        chosen_date = select_image_date(image_dates, current)
        if chosen_date is None:
            result[current] = (None, None)
        else:
            result[current] = _as_satellite_data(sector, records[chosen_date])
        current += timedelta(days=1)
    return result


def fetch_latest_s2(sector: SectorModel, today: DateType, db: Session) -> None:
    """Consulta GEE para la imagen S2 mas reciente y la persiste si no esta duplicada.

    Si la fila para esa fecha ya existe pero sin thumbnail, lo actualiza.
    """
    if not sector.polygon_geojson:
        return
    try:
        new_indices = get_satellite_indices(sector.polygon_geojson, today)
        if new_indices is None:
            return
        existing = (
            db.query(SatelliteRecord)
            .filter(
                SatelliteRecord.sector_id == sector.id,
                SatelliteRecord.date == new_indices.image_date,
            )
            .first()
        )
        if existing is None:
            db.add(SatelliteRecord(
                sector_id=sector.id,
                date=new_indices.image_date,
                ndvi=new_indices.ndvi,
                cloud_cover_pct=new_indices.cloud_cover_pct,
                thumbnail_png=new_indices.thumbnail_png,
            ))
            db.flush()
            logger.info(
                "Nueva imagen S2 persistida: sector %d, fecha %s, NDVI %.4f",
                sector.id, new_indices.image_date, new_indices.ndvi,
            )
        elif existing.thumbnail_png is None and new_indices.thumbnail_png is not None:
            existing.thumbnail_png = new_indices.thumbnail_png
            db.flush()
            logger.info(
                "Thumbnail agregado a registro existente del %s (sector %d)",
                new_indices.image_date, sector.id,
            )
    except RuntimeError as e:
        logger.warning(
            "No se pudo obtener NDVI de GEE para sector %d: %s. "
            "Se usará registro existente o Kc tabular.", sector.id, e,
        )



def prefetch_s2_for_range(
    sector: SectorModel, start_date: DateType, end_date: DateType, db: Session
) -> None:
    """Trae todas las imagenes S2 del periodo y las persiste antes del backfill.

    Amplia la ventana NDVI_MAX_AGE_DAYS hacia atras para que el primer dia
    tambien pueda usar Kc dinamico.
    """
    if not sector.polygon_geojson:
        return
    lookback_start = start_date - timedelta(days=NDVI_MAX_AGE_DAYS)
    try:
        indices_list = get_satellite_indices_for_range(
            sector.polygon_geojson, lookback_start, end_date,
        )
    except RuntimeError as e:
        logger.warning(
            "No se pudieron traer imágenes S2 para sector %d: %s. "
            "Backfill usará Kc tabular.", sector.id, e,
        )
        return
    if not indices_list:
        logger.info(
            "Sin imágenes S2 para sector %d entre %s y %s",
            sector.id, lookback_start, end_date,
        )
        return
    persisted = 0
    for idx in indices_list:
        existing = (
            db.query(SatelliteRecord)
            .filter(
                SatelliteRecord.sector_id == sector.id,
                SatelliteRecord.date == idx.image_date,
            )
            .first()
        )
        if existing is None:
            db.add(SatelliteRecord(
                sector_id=sector.id,
                date=idx.image_date,
                ndvi=idx.ndvi,
                cloud_cover_pct=idx.cloud_cover_pct,
                thumbnail_png=None,
            ))
            persisted += 1
    db.flush()
    logger.info(
        "Prefetch S2 sector %d: %d imagenes nuevas persistidas (rango %s a %s)",
        sector.id, persisted, lookback_start, end_date,
    )