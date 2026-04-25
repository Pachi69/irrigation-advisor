from datetime import date as DateType, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.field import Field as FieldModel, FieldStatus
from app.models.satellite_record import SatelliteRecord, SatelliteSource
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationResponse, RecommendationHistoryItem
from app.schemas.calculation import EToResult
from app.schemas.satellite import SatelliteData
from app.auth.dependencies import get_current_user
from app.ingestion.climate import get_climate_data, get_forecast
from app.ingestion.satellite import get_satellite_indices
from app.calculation.eto import calculate_eto
from app.calculation.kc import calculate_kc
from app.calculation.water_balance import calculate_water_balance
from app.calculation.crop_params import get_root_depth, get_depletion_factor
from app.calculation.urgency import calculate_urgency

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
    """Genera la recomendacion de riego para el campo indicado.
    
    Ejecuta el pipeline completo:
        clima -> ETo -> NDVI -> Kc -> Balance hidrico -> urgencia
        
    El deficit acumulado se persiste en el campo para que cada llamada
    continue desde el estado real del suelo del dia anterior.
    """
    field = _get_active_field(field_id, current_user, db)
    today = DateType.today()
    yesterday = today - timedelta(days=1)

    # Datos climaticos de ayer
    try:
        climate = get_climate_data(field.latitude, field.longitude, yesterday)
        if climate.eto_reference_mm is None:
            eto_result = calculate_eto(climate, field.latitude, yesterday, field.elevation_m)
            climate = climate.model_copy(update={"eto_reference_mm": eto_result.eto_mm})
    except (ValueError, RuntimeError) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudieron obtener datos climaticos: {e}"
        )
    
    eto = EToResult(eto_mm=climate.eto_reference_mm)

    # NDVI mas reciente (maximo NDVI_MAX_AGE_DAYS dias)
    cutoff = today - timedelta(days=NDVI_MAX_AGE_DAYS)
    sat_record = (
        db.query(SatelliteRecord)
        .filter(
            SatelliteRecord.field_id == field_id,
            SatelliteRecord.date >= cutoff,
        )
        .order_by(SatelliteRecord.date.desc())
        .first()
    )

    if sat_record is None and field.polygon_geojson:
        try:
            indices = get_satellite_indices(field.polygon_geojson, yesterday)
            if indices is not None:
                sat_record = SatelliteRecord(
                    field_id=field_id,
                    date=yesterday,
                    source=SatelliteSource.sentinel2,
                    ndvi=indices.ndvi,
                    ndwi=indices.ndwi,
                    evi=indices.evi,
                    cloud_cover_pct=indices.cloud_cover_pct,
                    moisture_event_detected=False,
                )
                db.add(sat_record)
                logger.info("NDVI obtenido de GEE y guardado: %.4f", indices.ndvi)
        except RuntimeError as e:
            logger.warning("No se pudo obtener NDVI de GEE: %s. Se usara Kc tabular.", e)

    satellite_data = None
    ndvi_date = None
    if sat_record:
        satellite_data = SatelliteData(
            field_id=field_id,
            date=sat_record.date,
            source=sat_record.source,
            ndvi=sat_record.ndvi,
        )
        ndvi_date = sat_record.date

    # Coeficiente de cultivo
    kc_result = calculate_kc(
        crop_type=field.crop_type,
        planting_date=field.planting_date,
        current_date=yesterday,
        satellite_data=satellite_data,
    )

    # Balance hidrico
    previous_deficit = field.last_deficit_mm if field.last_deficit_mm is not None else 0.0

    balance = calculate_water_balance(
        eto=eto,
        kc=kc_result,
        precipitation_mm=climate.precipitation_mm,
        previous_deficit_mm=previous_deficit,
        soil_type=field.soil_type,
        root_depth_m=get_root_depth(field.crop_type),
        depletion_factor_p=get_depletion_factor(field.crop_type),
    )

    # Persistir nuevo deficit
    field.last_deficit_mm = balance.water_deficit_mm
    field.last_deficit_date = yesterday

    # Pronostico (3 dias)
    try:
        forecast = get_forecast(field.latitude, field.longitude, days=3)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudieron obtener pronosticos: {e}"
        )
    
    # Urgencia
    urgency = calculate_urgency(balance, forecast, kc_result)

    # Persistir recomendacion (upsert por field_id + date)
    rec = (
        db.query(Recommendation)
        .filter(Recommendation.field_id == field_id, Recommendation.date == yesterday)
        .first()
    )
    if rec is None:
        rec = Recommendation(field_id=field_id, date=yesterday)
        db.add(rec)

    rec.eto_mm = eto.eto_mm
    rec.kc = kc_result.kc
    rec.kc_source = kc_result.source
    rec.etc_mm = eto.eto_mm * kc_result.kc
    rec.water_deficit_mm = balance.water_deficit_mm
    rec.ks = balance.ks
    rec.phenological_stage = kc_result.phenological_stage
    rec.recommended_irrigation_mm = urgency.recommended_irrigation_mm
    rec.urgency = urgency.urgency_level
    rec.reason = urgency.reason
    rec.precipitation_mm = climate.precipitation_mm
    rec.confidence = urgency.confidence

    db.commit()
    logger.info("Recomendacion persistida - campo %d fecha %s urgencia %s", field_id, yesterday, urgency.urgency_level)

    return RecommendationResponse(
        field_id=field_id,
        date=yesterday,
        urgency_level=urgency.urgency_level,
        recommended_irrigation_mm=urgency.recommended_irrigation_mm,
        reason=urgency.reason,
        confidence=urgency.confidence,
        water_deficit_mm=balance.water_deficit_mm,
        ks=balance.ks,
        taw_mm=balance.taw_mm,
        raw_mm=balance.raw_mm,
        eto_mm=eto.eto_mm,
        kc=kc_result.kc,
        kc_source=kc_result.source,
        phenological_stage=kc_result.phenological_stage,
        ndvi=satellite_data.ndvi if satellite_data else None,
        ndvi_date=ndvi_date,
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