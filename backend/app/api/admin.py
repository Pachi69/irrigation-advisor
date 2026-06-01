from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

import logging

from app.database import get_db
from app.models.user import User
from app.models.field import Field as FieldModel
from app.models.sector import Sector as SectorModel
from app.models.enums import SectorStatus
from app.schemas.admin import FieldAdminView
from app.schemas.sector import SectorPublic, SectorUpdate
from app.auth.dependencies import get_current_admin
from app.api._geo import setup_field_geo
from app.services.sector import update_field_geo, initialize_sector_balance
from app.api.sectors import enrich_sector, build_field_public


router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("/sectors/pending", response_model=list[FieldAdminView])
def list_pending_sectors(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Lista los campos que tienen al menos un sector pendiente de aprobacion.

      Cada campo trae todos sus sectores (cada uno con su status) para que el
      admin apruebe sector por sector.
    """
    fields = (
        db.query(FieldModel)
        .join(SectorModel, SectorModel.field_id == FieldModel.id)
        .options(joinedload(FieldModel.user))
        .filter(SectorModel.status == SectorStatus.pending)
        .order_by(FieldModel.created_at.asc())
        .distinct()
        .all()
    )
    return [build_field_public(f, db, FieldAdminView) for f in fields]


@router.post("/sectors/{sector_id}/approve", response_model=SectorPublic)
def approve_sector(
    sector_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Aprueba un sector: valida poligono, recalcula la geo del campo e inicializa
      su balance hidrico."""
    sector = db.query(SectorModel).filter(SectorModel.id == sector_id).first()
    if sector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sector no encontrado")
    
    if sector.status != SectorStatus.pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El sector ya fue aprobado")
    
    if not sector.polygon_geojson:
        raise HTTPException(status_code=status.HTTP_422_BAD_REQUEST, detail="El sector debe tener un poligono antes de aprobar")
    
    update_field_geo(sector.field, db)
    sector.status = SectorStatus.active
    db.commit()
    db.refresh(sector)

    try:
        initialize_sector_balance(sector, db)
    except Exception as e:
        logger.error("Initialize_sector_balance fallo para sector %d: %s", sector.id, e)
    
    db.refresh(sector)
    return enrich_sector(sector, db)


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
    
    for attr, value in data.model_dump(exclude_unset=True).items():
        setattr(sector, attr, value)
    
    if data.polygon_geojson is not None:
        _, _, sector.area_ha = setup_field_geo(data.polygon_geojson)
        update_field_geo(sector.field, db)

    db.commit()
    db.refresh(sector)
    return enrich_sector(sector, db)