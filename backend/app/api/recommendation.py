from typing import List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.field import Field as FieldModel
from app.models.satellite_record import SatelliteRecord
from app.models.daily_water_balance import DailyWaterBalance
from app.models.recommendation import Recommendation
from app.models.irrigation_confirmation import IrrigationConfirmation
from app.schemas.irrigation_confirmation import PendingConfirmationItem, IrrigationConfirmationCreate, IrrigationConfirmationResponse
from app.schemas.recommendation import RecommendationResponse, RecommendationHistoryItem
from app.services.recommendation import run_recommendation_pipeline, build_recommendation_response
from app.services.irrigation import confirm_irrigation
from app.api._helpers import owned_field, active_field


import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fields", tags=["recommendation"])


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


@router.get("/{field_id}/pending-confirmations", response_model=List[PendingConfirmationItem])
def get_pending_confirmations(field: FieldModel = Depends(owned_field), db: Session = Depends(get_db)):
    """Recomendaciones accionables (mm > 0) que aun no fueron confirmadas."""
    rows = (
        db.query(DailyWaterBalance, Recommendation)
        .join(Recommendation, Recommendation.water_balance_id == DailyWaterBalance.id)
        .outerjoin(
            IrrigationConfirmation,
            IrrigationConfirmation.recommendation_id == Recommendation.id
        )
        .filter(
            DailyWaterBalance.field_id == field.id,
            Recommendation.recommended_irrigation_mm > 0,
            IrrigationConfirmation.id.is_(None),
        )
        .order_by(DailyWaterBalance.date.desc())
        .all()
    )
    return [
        PendingConfirmationItem(
            recommendation_id=rec.id,
            date=wb.date,
            recommended_irrigation_mm=rec.recommended_irrigation_mm,
            urgency=rec.urgency,
            water_deficit_mm=wb.water_deficit_mm,
        )
        for wb, rec in rows
    ]

@router.post("/{field_id}/recommendations/{rec_id}/confirm", response_model=IrrigationConfirmationResponse, status_code=status.HTTP_201_CREATED)
def confirm_recommendation_irrigation(rec_id: int, data: IrrigationConfirmationCreate, field: FieldModel = Depends(owned_field), db: Session = Depends(get_db)):
    """Registra el riego aplicado para una recomendacion y recalcula el balance."""
    rec = (
        db.query(Recommendation)
        .join(DailyWaterBalance, Recommendation.water_balance_id == DailyWaterBalance.id)
        .filter(Recommendation.id == rec_id, DailyWaterBalance.field_id == field.id)
        .first()
    )
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recomendacion no encontrada")
    
    already = (
        db.query(IrrigationConfirmation)
        .filter(IrrigationConfirmation.recommendation_id == rec_id)
        .first()
    )
    if already:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recomendacion ya confirmada")
    
    if data.irrigation_date > date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La fecha de riego no puede ser futura")
    
    return confirm_irrigation(field, rec, data.irrigation_date, data.applied_irrigation_mm, db)
