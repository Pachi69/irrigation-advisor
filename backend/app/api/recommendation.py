from typing import List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.sector import Sector as SectorModel
from app.models.satellite_record import SatelliteRecord
from app.models.daily_water_balance import DailyWaterBalance
from app.models.recommendation import Recommendation
from app.models.irrigation_confirmation import IrrigationConfirmation
from app.schemas.irrigation_confirmation import PendingConfirmationItem, IrrigationConfirmationCreate, IrrigationConfirmationResponse
from app.schemas.recommendation import RecommendationResponse, RecommendationHistoryItem
from app.services.recommendation import run_recommendation_pipeline, build_recommendation_response
from app.services.irrigation import confirm_irrigation
from app.calculation.irrigation import time_min_to_mm, volume_m3_to_mm, efficiency_for
from app.api._helpers import owned_sector, active_sector


import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sectors", tags=["recommendation"])


@router.get("/{sector_id}/recommendation", response_model=RecommendationResponse)
def get_recommendation(
    sector: SectorModel = Depends(active_sector),
    db: Session = Depends(get_db),
):
    """Devuelve la ultima recomendacion guardada. Solo recalcula si no existe ninguna."""

    existing_wb = (
        db.query(DailyWaterBalance)
        .filter(DailyWaterBalance.sector_id == sector.id)
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
                    SatelliteRecord.sector_id == sector.id,
                    SatelliteRecord.date == existing_wb.ndvi_date,
                )
                .first()
            )
            if sat_rec:
                cloud_cover = sat_rec.cloud_cover_pct
        return build_recommendation_response(existing_wb, existing_wb.recommendation, cloud_cover)

    try:
        return run_recommendation_pipeline(sector, db)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))


@router.get("/{sector_id}/recommendations", response_model=List[RecommendationHistoryItem])
def get_recommendation_history(
    sector: SectorModel = Depends(owned_sector),
    db: Session = Depends(get_db),
):
    """Devuelve el historial de recomendaciones del campo, ordenado del mas reciente al mas antiguo""" 
    balances = (
        db.query(DailyWaterBalance)
        .filter(DailyWaterBalance.sector_id == sector.id)
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
            volume_m3=b.recommendation.volume_m3,
            time_min=b.recommendation.time_min,
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


@router.get("/{sector_id}/pending-confirmations", response_model=List[PendingConfirmationItem])
def get_pending_confirmations(sector: SectorModel = Depends(owned_sector), db: Session = Depends(get_db)):
    """Recomendaciones accionables (mm > 0) que aun no fueron confirmadas."""
    rows = (
        db.query(DailyWaterBalance, Recommendation)
        .join(Recommendation, Recommendation.water_balance_id == DailyWaterBalance.id)
        .outerjoin(
            IrrigationConfirmation,
            IrrigationConfirmation.recommendation_id == Recommendation.id
        )
        .filter(
            DailyWaterBalance.sector_id == sector.id,
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
            time_min=rec.time_min,
            volume_m3=rec.volume_m3,
            urgency=rec.urgency,
            water_deficit_mm=wb.water_deficit_mm,
        )
        for wb, rec in rows
    ]

@router.post("/{sector_id}/recommendations/{rec_id}/confirm", response_model=IrrigationConfirmationResponse, status_code=status.HTTP_201_CREATED)
def confirm_recommendation_irrigation(rec_id: int, data: IrrigationConfirmationCreate, sector: SectorModel = Depends(active_sector), db: Session = Depends(get_db)):
    """Registra el riego aplicado (en tiempo) para una recomendacion y recalcula el balance.
    
    El tiempo o volumen se convierte a lamina neta (mm) con los datos del sector antes de persistir:
    el balance hidrico siempre trabaja en mm netos.
    """
    rec = (
        db.query(Recommendation)
        .join(DailyWaterBalance, Recommendation.water_balance_id == DailyWaterBalance.id)
        .filter(Recommendation.id == rec_id, DailyWaterBalance.sector_id == sector.id)
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
    
    eff = efficiency_for(sector.irrigation_type)
    if data.applied_volume_m3 is not None:
        applied_mm = volume_m3_to_mm(data.applied_volume_m3, sector.area_ha, eff)
    else:
        if not sector.flow_rate_ls_ha:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El sector no tiene una caudal cargado, confirma el riego por volumen (m3)")
        applied_mm = time_min_to_mm(data.applied_time_min, sector.flow_rate_ls_ha, eff)
    
    return confirm_irrigation(sector, rec, data.irrigation_date, applied_mm, db)
