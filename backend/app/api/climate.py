from datetime import date as DateType, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.field import Field as FieldModel, FieldStatus
from app.schemas.climate import ClimateData, ForecastDay
from app.auth.dependencies import get_current_user
from app.ingestion.climate import get_climate_data, get_forecast
from app.calculation.eto import calculate_eto

router = APIRouter(prefix="/fields", tags=["climate"])

def _get_active_field(field_id: int, current_user: User, db: Session) -> FieldModel:
    """Obtiene un campo activo verificado que pertenezca al usuario actual.
    Raises:
        404 si el campo no existe o no pertenece al usuario
        409 si el campo aun no fue aprobado (sin poligono asignado)
    """
    field = db.query(FieldModel).filter(FieldModel.id == field_id).first()
    if not field or field.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campo no encontrado")
    if field.status != FieldStatus.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El campo aun no fue aprobado (sin poligono asignado)"
        )
    return field


@router.get("/{field_id}/climate", response_model=ClimateData)
def get_field_climate(
    field_id: int,
    target_date: Optional[DateType] = Query(
        default=None,
        alias="date",
        description="Fecha YYYY-MM-DD (por defecto: ayer)",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
): 
    """Devuelve los datos climaticos de un dia para el campo indicado.
    
    - Por defecto consulta el dia de ayer.
    - Acepta fechas de hasta 92 dias atras.
    - El campo debe estar activo (poligono asignado por admin)"""
    field = _get_active_field(field_id, current_user, db)
    resolved_date = target_date if target_date is not None else DateType.today() - timedelta(days=1)

    try:
        climate = get_climate_data(field.latitude, field.longitude, resolved_date)
        if climate.eto_reference_mm is None:
            eto_result = calculate_eto(climate, field.latitude, resolved_date, field.elevation_m)
            climate = climate.model_copy(update={"eto_reference_mm": eto_result.eto_mm})
        return climate
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    

@router.get("/{field_id}/forecast", response_model=list[ForecastDay])
def get_field_forecast(
    field_id: int,
    days: int = Query(default=5, ge= 1, le=16, description="Dias a pronosticar [1-16]"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Devuelve el pronostico de los proximos N dias para el campo indicado.
    - Por defecto 5 dias.
    - El campo debe estar activo (poligono asignado por admin)
    """
    field = _get_active_field(field_id, current_user, db)

    try:
        return get_forecast(field.latitude, field.longitude, days)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))