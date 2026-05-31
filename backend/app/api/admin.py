from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

import logging

from app.database import get_db
from app.models.user import User
from app.models.field import Field as FieldModel
from app.models.sector import Sector as SectorModel
from app.models.enums import FieldStatus
from app.schemas.admin import FieldAdminView
from app.schemas.sector import SectorPublic, SectorUpdate
from app.auth.dependencies import get_current_admin
from app.api._geo import setup_field_geo
from app.ingestion.climate import get_elevation
from app.services.field import initialize_field_balance
from app.services.sector import update_field_geo
from app.api.sectors import enrich_sector, build_field_public


router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("/fields/pending", response_model=list[FieldAdminView])
def list_pending_fields(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Lista todos los campos pendientes de aprobacion, de cualquier usuario."""
    fields = (
        db.query(FieldModel)
        .options(joinedload(FieldModel.user))
        .filter(FieldModel.status == FieldStatus.pending)
        .order_by(FieldModel.created_at.asc())
        .all()
    )
    return [build_field_public(f, db, FieldAdminView) for f in fields]


@router.post("/fields/{field_id}/approve", response_model=FieldAdminView)
def approve_field(
    field_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Aprueba un campo: calcula centroide desde sus sectores y activa el balance."""
    field = (
        db.query(FieldModel)
        .options(joinedload(FieldModel.user))
        .filter(FieldModel.id == field_id)
        .first()
    )
    if field is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campo no encontrado"
        )
    if field.status != FieldStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El campo ya fue procesado (estado actual: {field.status.value})",
        )
    if not any(s.polygon_geojson for s in field.sectors):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El campo debe tener al menos un sector con poligono antes de aprobar.",
        )
    
    update_field_geo(field, db)
    if field.elevation_m is None and field.latitude:
        field.elevation_m = get_elevation(field.latitude, field.longitude)
    field.status = FieldStatus.active
    db.commit()
    db.refresh(field)

    try:
        initialize_field_balance(field, db)
    except Exception as e:
        logger.error("initialize_field_balance fallo para campo %d: %s", field.id, e)

    return build_field_public(field, db, FieldAdminView)


@router.patch("/sectors/{sector_id}", response_model=SectorPublic)
def admin_update_sector(
    sector_id: int,
    data: SectorUpdate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """El admin puede editar cualquier sector (corregir poligono, variedad, etc.)."""
    sector = db.query(SectorModel).filter(SectorModel.id == sector_id).first()
    if sector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sector no encontrado")
    
    for attr, value in data.model_dump(exclude_none=True).items():
        setattr(sector, attr, value)
    
    if data.polygon_geojson is not None:
        _, _, sector.area_ha, _ = setup_field_geo(data.polygon_geojson)
        update_field_geo(sector.field, db)

    db.commit()
    db.refresh(sector)
    return enrich_sector(sector, db)