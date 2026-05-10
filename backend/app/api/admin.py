from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User
from app.models.field import Field as FieldModel, FieldStatus
from app.schemas.admin import FieldApproval, FieldAdminView
from app.auth.dependencies import get_current_admin
from app.api._geo import validate_and_compute_centroid
from app.ingestion.soil import get_soil_type_from_coords
from app.ingestion.climate import get_elevation

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/fields/pending", response_model=list[FieldAdminView])
def list_pending_fields(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Lista todos los campos pendientes de aprobacion, de cualquier usuario."""
    return (
        db.query(FieldModel)
        .options(joinedload(FieldModel.user))
        .filter(FieldModel.status == FieldStatus.pending)
        .order_by(FieldModel.created_at.asc())
        .all()
    )

@router.post("/fields/{field_id}/approve", response_model=FieldAdminView)
def approve_field(
    field_id: int,
    data: FieldApproval,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Aprueba un campo asignandole poligono GeoJSON.
    Calcula el centroide y activa el campo."""
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
    try:
        latitude, longitude = validate_and_compute_centroid(data.polygon_geojson)
        detected_soil = get_soil_type_from_coords(latitude, longitude)
        if detected_soil is not None:
            field.soil_type = detected_soil
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"GeoJSON invalido: {e}",
        )
    
    field.polygon_geojson = data.polygon_geojson
    field.latitude = latitude
    field.longitude = longitude
    field.elevation_m = get_elevation(latitude, longitude)
    field.status = FieldStatus.active
    db.commit()
    db.refresh(field)
    return field


@router.post("/trigger-notifications")
def trigger_notifications_now(_admin: User = Depends(get_current_admin)):
    """[TEST] Genera recomendaciones de hoy y dispara notificaciones."""
    from app.jobs.recommendation_job import generate_daily_recommendations
    from app.jobs.notification_job import send_daily_recommendation_notifications
    generate_daily_recommendations()
    send_daily_recommendation_notifications()
    return {"detail": "Recomendaciones generadas y notificaciones enviadas, revisar logs"}