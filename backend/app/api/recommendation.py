from datetime import date as DateType
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session


from app.database import get_db
from app.models.user import User
from app.models.field import Field as FieldModel, FieldStatus
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationResponse, RecommendationHistoryItem
from app.auth.dependencies import get_current_user
from app.services.recommendation import run_recommendation_pipeline


import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fields", tags=["recommendation"])

NDVI_MAX_AGE_DAYS = 30

def _get_active_field(field_id: int, current_user: User, db: Session) -> FieldModel:
    field = db.query(FieldModel).filter(FieldModel.id == field_id).first()
    if not field or field.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campo no encontrado")
    if field.status != FieldStatus.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El campo aun no fue aprobado (sin poligono asignado)"
        )
    return field


@router.get("/{field_id}/recommendation", response_model=RecommendationResponse)
def get_recommendation(
    field_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Genera y persiste la recomendacion de riego para el campo indicado."""
    field = _get_active_field(field_id, current_user, db)
    try:
        return run_recommendation_pipeline(field, db)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.get("/{field_id}/recommendations", response_model=List[RecommendationHistoryItem])
def get_recommendation_history(
    field_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Devuelve el historial de recomendaciones del campo, ordenado del mas reciente al mas antiguo"""
    field = db.query(FieldModel).filter(FieldModel.id == field_id).first()
    if not field or field.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campo no encontrado")
    
    records = (
        db.query(Recommendation)
        .filter(Recommendation.field_id == field_id)
        .order_by(Recommendation.date.desc())
        .limit(90)
        .all()
    )
    return records