from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date as date_type

from app.database import get_db
from app.models.user import User
from app.models.field import Field as FieldModel
from app.models.enums import FieldStatus
from app.models.alert import Alert
from app.schemas.field import FieldCreate, FieldPublic, FieldUpdate
from app.schemas.alert import AlertPublic
from app.auth.dependencies import get_current_user
from app.api._helpers import owned_field
from app.api.sectors import build_field_public

router = APIRouter(prefix="/fields", tags=["fields"])


@router.post("", response_model=FieldPublic, status_code=status.HTTP_201_CREATED)
def create_field(
    data: FieldCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea un campo asociado al usuario autenticado"""
    existing_pending = (
        db.query(FieldModel)
        .filter(
            FieldModel.user_id == current_user.id,
            FieldModel.status == FieldStatus.pending,
        )
        .first()
    )
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Ya tenes un campo pendiente de aprobacion. Espera a que sea procesado antes de registrar otro"
        )

    field = FieldModel(user_id=current_user.id, name=data.name, soil_type=data.soil_type)
    db.add(field)
    db.commit()
    db.refresh(field)
    return build_field_public(field, db)

@router.get("", response_model=list[FieldPublic])
def list_my_fields(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista los campos asociados al usuario autenticado."""
    fields = (
        db.query(FieldModel)
        .filter(FieldModel.user_id == current_user.id)
        .order_by(FieldModel.created_at.desc())
        .all()
    )
    return [build_field_public(f, db) for f in fields]


@router.get("/{field_id}", response_model=FieldPublic)
def get_my_field(field: FieldModel = Depends(owned_field), db: Session = Depends(get_db)):
    return build_field_public(field, db)


@router.patch("/{field_id}", response_model=FieldPublic)
def update_field(
    data: FieldUpdate,
    field: FieldModel = Depends(owned_field),
    db: Session = Depends(get_db),
):
    """Actualiza los datos editables de un campo del usuario autenticado."""    
    for attr, value in data.model_dump(exclude_none=True).items():
        setattr(field, attr, value)

    db.commit()
    db.refresh(field)
    return build_field_public(field, db)


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_field(field: FieldModel = Depends(owned_field), db: Session = Depends(get_db)):
    """Elimina un campo del usuario autenticado y sus registros asociados (cascada)."""
    db.delete(field)
    db.commit()


@router.get("/{field_id}/alerts", response_model=list[AlertPublic])
def get_field_alerts(
    field: FieldModel = Depends(owned_field),
    db: Session = Depends(get_db),
):
    """Retorna las alertas del dia mas proximo (date > today) para un campo"""
    today = date_type.today()
    alerts = (
        db.query(Alert)
        .filter(Alert.field_id == field.id, Alert.date > today)
        .order_by(Alert.date.asc())
        .all()
    )

    if not alerts:
        return []
    
    nearest_date = alerts[0].date
    return [a for a in alerts if a.date == nearest_date]

