from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.field import Field as FieldModel
from app.models.sector import Sector as SectorModel
from app.models.enums import FieldStatus
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

def active_field(field: FieldModel = Depends(owned_field)) -> FieldModel:
    if field.status != FieldStatus.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El campo aun no fue aprobado (sin poligono asignado)")
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
    if sector.field.status != FieldStatus.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El campo aun no fue aprobado")
    return sector

def iter_active_sectors(db: Session) -> list[SectorModel]:
    """Sectores de campos activos (job de recomendacion)"""
    return (
        db.query(SectorModel)
        .join(FieldModel, SectorModel.field_id == FieldModel.id)
        .filter(FieldModel.status == FieldStatus.active)
        .all()
    )

def iter_active_fields(db: Session) -> list[FieldModel]:
    """Campos activos (job de alertas)"""
    return (
        db.query(FieldModel)
        .filter(FieldModel.status == FieldStatus.active)
        .all()
    )