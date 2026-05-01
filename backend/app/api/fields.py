from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date as date_type, timedelta

from app.database import get_db
from app.models.user import User
from app.models.field import Field as FieldModel, FieldStatus
from app.models.alert import Alert
from app.models.recommendation import Recommendation
from app.models.satellite_record import SatelliteRecord
from app.schemas.field import FieldCreate, FieldPublic, FieldUpdate, FieldChartData, DeficitPoint, NdviPoint
from app.schemas.alert import AlertPublic
from app.auth.dependencies import get_current_user
from app.calculation.crop_params import get_depletion_factor
from app.api._geo import validate_and_compute_centroid

router = APIRouter(prefix="/fields", tags=["fields"])

@router.post("", response_model=FieldPublic, status_code=status.HTTP_201_CREATED)
def create_field(
    data: FieldCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crea un campo asociado al usuario autenticado. Queda en estado 'pendind'
    hasta que un admin le asigne un polígono."""
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
    
    latitude, longitude = None, None
    if data.polygon_geojson:
        try:
            latitude, longitude = validate_and_compute_centroid(data.polygon_geojson)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=f"GeoJSON invalido: {e}"
            )

    field = FieldModel(
        user_id=current_user.id,
        name=data.name,
        crop_type=data.crop_type,
        area_ha=data.area_ha,
        irrigation_type=data.irrigation_type,
        soil_type=data.soil_type,
        has_hail_net=data.has_hail_net,
        planting_date=data.planting_date,
        polygon_geojson=data.polygon_geojson,
        latitude=latitude,
        longitude=longitude,
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


@router.get("/{field_id}/alerts", response_model=list[AlertPublic])
def get_field_alerts(
    field_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna las alertas del dia mas proximo (date > today) para un campo"""
    field = (
        db.query(FieldModel)
        .filter(FieldModel.id == field_id, FieldModel.user_id == current_user.id)
        .first()
    )
    if field is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campo no encontrado")
    
    today = date_type.today()
    alerts = (
        db.query(Alert)
        .filter(Alert.field_id == field_id, Alert.date > today)
        .order_by(Alert.date.asc())
        .all()
    )

    if not alerts:
        return []
    
    nearest_date = alerts[0].date
    return [a for a in alerts if a.date == nearest_date]


@router.patch("/{field_id}", response_model=FieldPublic)
def update_field(
    field_id: int,
    data: FieldUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualiza los datos editables de un campo del usuario autenticado."""
    field = (
        db.query(FieldModel)
        .filter(FieldModel.id == field_id, FieldModel.user_id == current_user.id)
        .first()
    )
    if field is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campo no encontrado")
    
    for attr, value in data.model_dump(exclude_none=True).items():
        setattr(field, attr, value)

    db.commit()
    db.refresh(field)
    return field

@router.get("/{field_id}/chart", response_model=FieldChartData)
def get_field_chart_data(
    field_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Devuelve series temporales de deficit hidrico % y NDVI para el grafico historico."""
    field = (
        db.query(FieldModel)
        .filter(FieldModel.id == field_id, FieldModel.user_id == current_user.id)
        .first()
    )
    if field is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campo no encontrado")
    
    cutoff = date_type.today() - timedelta(days=90)

    recommendations = (
        db.query(Recommendation)
        .filter(
            Recommendation.field_id == field_id,
            Recommendation.date >= cutoff,
            Recommendation.taw_mm != None,
            )
        .order_by(Recommendation.date.asc())
        .all()
    )

    satellite_records = (
        db.query(SatelliteRecord)
        .filter(
            SatelliteRecord.field_id == field_id,
            SatelliteRecord.date >= cutoff,
        )
        .order_by(SatelliteRecord.date.asc())
        .all()
    )

    deficit_series = [
        DeficitPoint(
            date=rec.date,
            pct=round(min(100, (rec.water_deficit_mm / rec.taw_mm) * 100), 1),
        )
        for rec in recommendations
        if rec.taw_mm and rec.taw_mm > 0
    ]

    ndvi_series = [
        NdviPoint(date=rec.date, value=round(rec.ndvi, 4))
        for rec in satellite_records
        if rec.ndvi is not None
    ]

    return FieldChartData(deficit=deficit_series, ndvi=ndvi_series, raw_threshold_pct=round(get_depletion_factor(field.crop_type) * 100, 1),)