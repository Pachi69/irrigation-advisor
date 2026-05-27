"""Servicio de datos satelitales: busqueda y persistencia de imagenes S2."""
from datetime import date as DateType, timedelta

import logging

from sqlalchemy.orm import Session

from app.models.field import Field as FieldModel
from app.models.satellite_record import SatelliteRecord
from app.schemas.satellite import SatelliteData
from app.ingestion.satellite import get_satellite_indices, get_satellite_indices_for_range

logger = logging.getLogger(__name__)

NDVI_MAX_AGE_DAYS = 15
SAT_FORWARD_FILL_MAX_DAYS = 5 # tope para el forward-fill del hueco inicial

def get_satellite_data_for_date(
    field: FieldModel, target_date: DateType, db: Session
) -> tuple[SatelliteData | None, DateType | None]:
    """Devuelve el NDVI vigente a una fecha (mas reciente con fecha <= target_date,
    dentro de los ultimos NDVI_MAX_AGE_DAYS dias)."""
    cutoff = target_date - timedelta(days=NDVI_MAX_AGE_DAYS)
    sat_record = (
        db.query(SatelliteRecord)
        .filter(
            SatelliteRecord.field_id == field.id,
            SatelliteRecord.date <= target_date,
            SatelliteRecord.date >= cutoff,
        )
        .order_by(SatelliteRecord.date.desc())
        .first()
    )
    if sat_record is None:
        return None, None
    return (
        SatelliteData(
            field_id=field.id, date=sat_record.date,
            ndvi=sat_record.ndvi, cloud_cover_pct=sat_record.cloud_cover_pct,
        ),
        sat_record.date,
    )

def get_satellite_data_for_range(
    field: FieldModel, start_date: DateType, end_date: DateType, db: Session
) -> dict[DateType, tuple[SatelliteData | None, DateType | None]]:
    """Resuelve el dato satelital vigente para cada dia de un rango, en memoria.

    Matching:
      - Carry-forward: cada dia usa la imagen mas reciente con fecha <= dia,
        siempre que no tenga mas de NDVI_MAX_AGE_DAYS (15) dias.
      - Forward-fill del hueco inicial: si un dia no tiene ninguna imagen previa,
        usa la primera imagen disponible solo si esta dentro de
        SAT_FORWARD_FILL_MAX_DAYS (5) dias; sino None (Kc tabular).

    Returns:
        dict {fecha: (SatelliteData | None, fecha_imagen | None)} con una
        entrada por cada dia del rango.
    """
    # Traer todo el rango + lookback hacia atras para que el carry-forward del primer dia tambien funcione.
    lookback_start = start_date - timedelta(days=NDVI_MAX_AGE_DAYS)
    records = (
        db.query(SatelliteRecord)
        .filter(
            SatelliteRecord.field_id == field.id,
            SatelliteRecord.date >= lookback_start,
            SatelliteRecord.date <= end_date,
        )
        .order_by(SatelliteRecord.date.asc())
        .all()
    )

    result: dict[DateType, tuple[SatelliteData | None, DateType | None]] = {}

    if not records:
        current = start_date
        while current <= end_date:
            result[current] = (None, None)
            current += timedelta(days=1)
        return result
    
    first_record = records[0]
    ptr = 0
    current = start_date
    while current <= end_date:
        # Avanzar el puntero mientras la imagen siga siendo <= current
        while ptr < len(records) and records[ptr].date <= current:
            ptr += 1

        chosen = None
        if ptr > 0:
            # records[ptr-1] = ultima imagen con fecha <= current (carry-forward)
            candidate = records[ptr - 1]
            if (current - candidate.date).days <= NDVI_MAX_AGE_DAYS:
                chosen = candidate
        else:
            # Hueco inicial: no hay imagen previa -> forward fill con la primera
            if (first_record.date - current).days <= SAT_FORWARD_FILL_MAX_DAYS:
                chosen = first_record

        if chosen is not None:
            result[current] = (
                SatelliteData(
                    field_id=field.id, date=chosen.date,
                    ndvi=chosen.ndvi, cloud_cover_pct=chosen.cloud_cover_pct,
                ),
                chosen.date
            )
        else:
            result[current] = (None, None)

        current += timedelta(days=1)

    return result


def fetch_latest_s2(field: FieldModel, today: DateType, db: Session) -> None:
    """Consulta GEE para la imagen S2 mas reciente y la persiste si no esta duplicada.

    Si la fila para esa fecha ya existe pero sin thumbnail, lo actualiza.
    """
    if not field.polygon_geojson:
        return
    try:
        new_indices = get_satellite_indices(field.polygon_geojson, today)
        if new_indices is None:
            return
        existing = (
            db.query(SatelliteRecord)
            .filter(
                SatelliteRecord.field_id == field.id,
                SatelliteRecord.date == new_indices.image_date,
            )
            .first()
        )
        if existing is None:
            db.add(SatelliteRecord(
                field_id=field.id,
                date=new_indices.image_date,
                ndvi=new_indices.ndvi,
                cloud_cover_pct=new_indices.cloud_cover_pct,
                thumbnail_png=new_indices.thumbnail_png,
            ))
            db.flush()
            logger.info(
                "Nueva imagen S2 persistida: fecha %s, NDVI %.4f",
                new_indices.image_date, new_indices.ndvi,
            )
        elif existing.thumbnail_png is None and new_indices.thumbnail_png is not None:
            existing.thumbnail_png = new_indices.thumbnail_png
            db.flush()
            logger.info("Thumbnail agregado a registro existente del %s", new_indices.image_date)
    except RuntimeError as e:
        logger.warning(
            "No se pudo obtener NDVI de GEE: %s. Se usara registro existente o Kc tabular.", e,
        )


def prefetch_s2_for_range(
    field: FieldModel, start_date: DateType, end_date: DateType, db: Session
) -> None:
    """Trae todas las imagenes S2 del periodo y las persiste antes del backfill.

    Amplia la ventana NDVI_MAX_AGE_DAYS hacia atras para que el primer dia
    tambien pueda usar Kc dinamico.
    """
    if not field.polygon_geojson:
        return
    lookback_start = start_date - timedelta(days=NDVI_MAX_AGE_DAYS)
    try:
        indices_list = get_satellite_indices_for_range(
            field.polygon_geojson, lookback_start, end_date,
        )
    except RuntimeError as e:
        logger.warning(
            "No se pudieron traer imagenes S2 para campo %d: %s. Backfill usara Kc tabular.",
            field.id, e,
        )
        return
    if not indices_list:
        logger.info(
            "Sin imagenes S2 disponibles para campo %d entre %s y %s",
            field.id, lookback_start, end_date,
        )
        return
    persisted = 0
    for idx in indices_list:
        existing = (
            db.query(SatelliteRecord)
            .filter(
                SatelliteRecord.field_id == field.id,
                SatelliteRecord.date == idx.image_date,
            )
            .first()
        )
        if existing is None:
            db.add(SatelliteRecord(
                field_id=field.id,
                date=idx.image_date,
                ndvi=idx.ndvi,
                cloud_cover_pct=idx.cloud_cover_pct,
                thumbnail_png=None,
            ))
            persisted += 1
    db.flush()
    logger.info(
        "Prefetch S2 campo %d: %d imagenes nuevas persistidas (rango %s a %s)",
        field.id, persisted, lookback_start, end_date,
    )