from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.field import Field as FieldModel
from app.schemas.field import FieldCreate, FieldPublic
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/fields", tags=["fields"])

@router.post("", response_model=FieldPublic, status_code=status.HTTP_201_CREATED)
def create_field(
    data: FieldCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea un campo asociado al usuario autenticado. Queda en estado 'pendind'
    hasta que un admin le asigne un polígono."""
    field = FieldModel(
        user_id=current_user.id,
        name=data.name,
        crop_type=data.crop_type,
        area_ha=data.area_ha,
        irrigation_type=data.irrigation_type,
        soil_type=data.soil_type,
        has_hail_net=data.has_hail_net,
        planting_date=data.planting_date,
        # status = pending (default del modelo)
        # polygon_geojson, elevation_m, latitude, longitude = None hasta HU-21
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field

@router.get("", response_model=list[FieldPublic])
def list_my_fields(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista los campos asociados al usuario autenticado."""
    return (
        db.query(FieldModel)
        .filter(FieldModel.user_id == current_user.id)
        .order_by(FieldModel.created_at.desc())
        .all()
    )

@router.get("/{field_id}", response_model=FieldPublic)
def get_my_field(
    field_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Detalle de un campo del usuario autenticado."""
    field = (
        db.query(FieldModel)
        .filter(FieldModel.id == field_id, FieldModel.user_id == current_user.id)
        .first()
    )
    if field is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campo no encontrado")
    return field
