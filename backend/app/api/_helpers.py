from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.field import Field as FieldModel
from app.models.sector import Sector as SectorModel
from app.models.enums import SectorStatus
from app.auth.dependencies import get_current_user


def owned_field(
    field_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FieldModel:
    field = db.query(FieldModel).filter(FieldModel.id == field_id).first()
    if not field or field.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campo no encontrado")
    return field

def located_field(field: FieldModel = Depends(owned_field)) -> FieldModel:
    if field.latitude is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El campo aun no tiene ubicacion (sin sectores con poligono)")
    return field

def owned_sector(
    sector_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SectorModel:
    sector = db.query(SectorModel).filter(SectorModel.id == sector_id).first()
    if not sector or sector.field.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sector no encontrado")
    return sector

def active_sector(sector: SectorModel = Depends(owned_sector)) -> SectorModel:
    if sector.status != SectorStatus.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El sector aun no fue aprobado")
    return sector

def iter_active_sectors(db: Session) -> list[SectorModel]:
    """Sectores aprobados (job de recomendacion)"""
    return (
        db.query(SectorModel)
        .filter(SectorModel.status == SectorStatus.active)
        .all()
    )

def iter_active_fields(db: Session) -> list[FieldModel]:
    """Campos con al menos un sector aprobado (job de alertas)"""
    return (
        db.query(FieldModel)
        .join(SectorModel, SectorModel.field_id == FieldModel.id)
        .filter(SectorModel.status == SectorStatus.active)
        .distinct()
        .all()
    )