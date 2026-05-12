from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.field import Field as FieldModel
from app.models.satellite_record import SatelliteRecord
from app.models.daily_water_balance import DailyWaterBalance
from app.schemas.recommendation import RecommendationResponse, RecommendationHistoryItem
from app.services.recommendation import run_recommendation_pipeline, build_recommendation_response
from app.api._helpers import owned_field, active_field


import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fields", tags=["recommendation"])

NDVI_MAX_AGE_DAYS = 30


@router.get("/{field_id}/recommendation", response_model=RecommendationResponse)
def get_recommendation(
    field: FieldModel = Depends(active_field),
    db: Session = Depends(get_db),
):
    """Devuelve la ultima recomendacion guardada. Solo recalcula si no existe ninguna."""

    existing_wb = (
        db.query(DailyWaterBalance)
        .filter(DailyWaterBalance.field_id == field.id)
        .options(joinedload(DailyWaterBalance.recommendation))
        .order_by(DailyWaterBalance.date.desc())
        .first()
    )

    if existing_wb and existing_wb.recommendation:
        cloud_cover = None
        if existing_wb.ndvi_date:
            sat_rec = (
                db.query(SatelliteRecord)
                .filter(
                    SatelliteRecord.field_id == field.id,
                    SatelliteRecord.date == existing_wb.ndvi_date,
                )
                .first()
            )
            if sat_rec:
                cloud_cover = sat_rec.cloud_cover_pct
        return build_recommendation_response(existing_wb, existing_wb.recommendation, cloud_cover)

    try:
        return run_recommendation_pipeline(field, db)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.get("/{field_id}/recommendations", response_model=List[RecommendationHistoryItem])
def get_recommendation_history(
    field: FieldModel = Depends(owned_field),
    db: Session = Depends(get_db),
):
    """Devuelve el historial de recomendaciones del campo, ordenado del mas reciente al mas antiguo""" 
    balances = (
        db.query(DailyWaterBalance)
        .filter(DailyWaterBalance.field_id == field.id)
        .options(joinedload(DailyWaterBalance.recommendation))
        .order_by(DailyWaterBalance.date.desc())
        .limit(90)
        .all()
    )
    return [
        RecommendationHistoryItem(
            id=b.recommendation.id,
            date=b.date,
            urgency=b.recommendation.urgency,
            recommended_irrigation_mm=b.recommendation.recommended_irrigation_mm,
            reason=b.recommendation.reason,
            confidence=b.recommendation.confidence,
            water_deficit_mm=b.water_deficit_mm,
            taw_mm=b.taw_mm,
            ks=b.ks,
            eto_mm=b.eto_mm,
            kc=b.kc,
            kc_source=b.kc_source,
            phenological_stage=b.phenological_stage,
        )
        for b in balances
        if b.recommendation is not None
    ]


@router.get("/{field_id}/satellite-image")
def get_satellite_image(
    field: FieldModel = Depends(owned_field),
    db: Session = Depends(get_db),
):
    """Devuelve el thumbnail PNG NDVI del ultimo registro satelital del campo."""
    record = (
        db.query(SatelliteRecord)
        .filter(
            SatelliteRecord.field_id == field.id,
            SatelliteRecord.thumbnail_png.is_not(None)
        )
        .order_by(SatelliteRecord.date.desc())
        .first()
    )

    if not record or not record.thumbnail_png:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagen satelital no encontrada")
    
    return Response(content=record.thumbnail_png, media_type="image/png")
