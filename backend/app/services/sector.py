"""Servicio de sectores: creacion, geo setup e inicializacion del balance."""
from datetime import date as DateType, timedelta
import logging

from sqlalchemy.orm import Session

from app.models.field import Field as FieldModel
from app.models.sector import Sector as SectorModel
from app.models.enums import SectorStatus
from app.schemas.sector import SectorCreate
from app.api._geo import setup_field_geo, validate_and_compute_centroid
from app.ingestion.soil import get_soil_type_from_coords


logger = logging.getLogger(__name__)


def create_sector(field: FieldModel, data: SectorCreate, db: Session) -> SectorModel:
    """Crea un sector dentro de un campo. Calcula centroide y area si viene con poligono."""
    area_ha = None

    if data.polygon_geojson:
        _, _, area_ha = setup_field_geo(data.polygon_geojson)
        
    sector = SectorModel(
        field_id=field.id,
        name=data.name,
        crop_type=data.crop_type,
        variety=data.variety,
        area_ha=area_ha,
        polygon_geojson=data.polygon_geojson,
        irrigation_type=data.irrigation_type,
        flow_rate_ls_ha=data.flow_rate_ls_ha,
        hail_net_type=data.hail_net_type,
        notification_frequency_days=data.notification_frequency_days,
        notification_hour=data.notification_hour,
        last_saturation_date=data.last_saturation_date,
    )
    db.add(sector)
    db.flush()
    return sector


def update_field_geo(field: FieldModel, db: Session) -> None:
    """Recalcula lat/lon del campo como promedio de los centroides de sus sectores.
    
    Detecta tipo de suelo y elevacion si aun no estan. Llamar tras crear/editar
    sectores con poligono o al aprobar el campo.
    """
    from app.ingestion.climate import get_elevation

    centroids = []
    for sector in field.sectors:
        if sector.polygon_geojson:
            try:
                lat, lon = validate_and_compute_centroid(sector.polygon_geojson)
                centroids.append((lat, lon))
            except ValueError:
                pass

    if not centroids:
        return
    
    field.latitude = sum(c[0] for c in centroids) / len(centroids)
    field.longitude = sum(c[1] for c in centroids) / len(centroids)

    if field.elevation_m is None:
        field.elevation_m = get_elevation(field.latitude, field.longitude)

    if field.soil_type is None:
        detected = get_soil_type_from_coords(field.latitude, field.longitude)
        if detected is not None:
            field.soil_type = detected

    db.flush()


def initialize_sector_balance(sector: SectorModel, db: Session) -> None:
    """Aprueba e inciailiza el balance hidrico de un sector.
    
    - Si last_saturation_date < hoy: asume Dr=0 ese dia y backfill hacia adelante.
    - Si last_saturation_date == hoy (o None): no hace backfill; asume Dr=0 hoy.

    Marca el sector como active
    """
    from app.services.recommendation import recompute_balance_from

    sector.status = SectorStatus.active
    today = DateType.today()
    saturation = sector.last_saturation_date

    if saturation is None or saturation >= today:
        sector.last_deficit_mm = 0.0
        sector.last_deficit_date = today
        db.commit()
        logger.info("Init balance sector %d: sin backfill (Dr=0 hoy)", sector.id)
        return
    
    recompute_balance_from(sector, saturation + timedelta(days=1), 0.0, db)
    logger.info(
        "Initi balance sector %d: recalculo desde %s (deficit final %.1f mm)",
        sector.id, saturation, sector.last_deficit_mm or 0.0,
    )