"""Servicio de recomendacion de riego: pipeline diario y persistencia."""
from datetime import date as DateType, timedelta

import logging

from sqlalchemy.orm import Session

from app.models.field import Field as FieldModel
from app.models.daily_water_balance import DailyWaterBalance
from app.models.recommendation import Recommendation
from app.models.enums import UrgencyLevel, ConfidenceLevel
from app.schemas.recommendation import RecommendationResponse
from app.ingestion.climate import get_forecast, get_climate_data_for_range
from app.calculation.urgency import calculate_urgency
from app.services.satellite import fetch_latest_s2, prefetch_s2_for_range, get_satellite_data_for_range
from app.services.water_balance import compute_balance_for_day, save_water_balance, compute_balance_from_data


logger = logging.getLogger(__name__)

def save_recommendation(
    wb: DailyWaterBalance,
    db: Session,
    *,
    urgency_level: UrgencyLevel,
    recommended_irrigation_mm: float,
    reason: str,
    confidence: ConfidenceLevel,
) -> Recommendation:
    """Crea o actualiza la recomendacion asociada a un DailyWaterBalance dado"""
    rec = (
        db.query(Recommendation)
        .filter(Recommendation.water_balance_id == wb.id)
        .first()
    )

    if rec is None:
        rec = Recommendation(water_balance_id=wb.id)
        db.add(rec)

    rec.recommended_irrigation_mm = recommended_irrigation_mm
    rec.urgency = urgency_level
    rec.reason = reason
    rec.confidence = confidence

    return rec

def build_recommendation_response(
    wb: DailyWaterBalance,
    rec: Recommendation,
    cloud_cover_pct: float | None = None,
) -> RecommendationResponse:
    """Construye RecommendationResponse plano desde los dos modelos separados."""
    return RecommendationResponse(
        field_id=wb.field_id,
        date=wb.date,
        urgency_level=rec.urgency,
        recommended_irrigation_mm=rec.recommended_irrigation_mm,
        reason=rec.reason,
        confidence=rec.confidence,
        water_deficit_mm=wb.water_deficit_mm,
        ks=wb.ks,
        taw_mm=wb.taw_mm,
        raw_mm=wb.raw_mm,
        eto_mm=wb.eto_mm,
        kc=wb.kc,
        kc_source=wb.kc_source,
        phenological_stage=wb.phenological_stage,
        ndvi=wb.ndvi,
        ndvi_date=wb.ndvi_date,
        cloud_cover_pct=cloud_cover_pct,
    )

def run_backfill(
    field: FieldModel, start_date: DateType, end_date: DateType, db: Session
) -> None:
    """Rellena los DailyWaterBalance + Recommendation faltantes entre start y end.
    
    Trae clima y satelite en batch y luego calcula dia por dia de forma secuencial,
    encadenando el deficit en memoria.
    
    Las recomendaciones retroactivas se guardan con urgencia 'low': el calculo
    de urgencia real solo aplica al dia en vivo.
    """
    if start_date > end_date:
        return
    
    # Prefetch satelital: asegura que las imagenes del periodo esten en la DB
    prefetch_s2_for_range(field, start_date, end_date, db)
    
    try:
        climate_by_date = get_climate_data_for_range(field.latitude, field.longitude, start_date, end_date)
    except (ValueError, RuntimeError) as e:
        logger.error("Backfill campo %d: no se pudo traer clima %s..%s: %s", field.id, start_date, end_date, e)
        return
    satellite_by_date = get_satellite_data_for_range(field, start_date, end_date, db)

    # Deficit inicial: el ultimo conocido del campo
    previous_deficit = field.last_deficit_mm or 0.0

    current = start_date
    while current <= end_date:
        climate = climate_by_date.get(current)
        if climate is None:
            logger.warning("Backfill campo %d: sin datos de clima para %s; dia omitido.", field.id, current,)
            current += timedelta(days=1)
            continue

        satellite_data, ndvi_date = satellite_by_date.get(current, (None, None))

        try: 
            climate, eto, satellite_data, ndvi_date, kc_result, balance = compute_balance_from_data(
                field, current,
                climate=climate,
                satellite_data=satellite_data,
                ndvi_date=ndvi_date,
                previous_deficit_mm=previous_deficit,
            )
            wb = save_water_balance(
                field, current, db,
                climate=climate, eto=eto, kc_result=kc_result, balance=balance,
                satellite_data=satellite_data, ndvi_date=ndvi_date,
            )
            save_recommendation(
                wb, db,
                urgency_level=UrgencyLevel.low,
                recommended_irrigation_mm=0.0,
                reason="Recalculado retroactivamente (backfill)",
                confidence=ConfidenceLevel.low,
            )
            db.flush()
            previous_deficit = balance.water_deficit_mm
            logger.info(
                "Backfill campo %d: dia %s, deficit %.2f mm",
                field.id, current, balance.water_deficit_mm,
            )
        except Exception as e:
            logger.error("Error en backfill dia %s campo %d: %s", current, field.id, e)
            # no break: el deficit no avanza, seguimos con el dia siguiente

        current += timedelta(days=1)

def run_recommendation_pipeline(field: FieldModel, db: Session) -> RecommendationResponse:
    """Ejecuta el pipeline completo de recomendacion para un campo activo.

    Raises:
        ValueError: si faltan variables climaticas obligatorias.
        RuntimeError: si falla la obtencion de pronostico climatico.
    """
    today = DateType.today()
    yesterday = today - timedelta(days=1)

    # Backfill: rellenar dias faltantes entre last_deficit_date y ayer
    if field.last_deficit_date is not None:
        run_backfill(
            field,
            field.last_deficit_date + timedelta(days=1),
            yesterday - timedelta(days=1),
            db,
        )

    # Obtener imagen S2 mas reciente
    fetch_latest_s2(field, today, db)

    # Calcular balance hidrico de ayer
    climate, eto, satellite_data, ndvi_date, kc_result, balance = compute_balance_for_day(
        field, yesterday, db
    )

    # Pronostico y urgencia (solo aplican al pipeline en vivo)
    forecast = get_forecast(field.latitude, field.longitude, days=3)
    urgency = calculate_urgency(balance, forecast, kc_result)

    # Persistir
    wb = save_water_balance(
        field, yesterday, db,
        climate=climate, eto=eto, kc_result=kc_result, balance=balance,
        satellite_data=satellite_data, ndvi_date=ndvi_date,
    )
    rec = save_recommendation(
        wb, db,
        urgency_level=urgency.urgency_level,
        recommended_irrigation_mm=urgency.recommended_irrigation_mm,
        reason=urgency.reason,
        confidence=urgency.confidence,
    )

    db.commit()
    logger.info(
        "Recomendacion persistida - campo %d fecha %s urgencia %s",
        field.id, yesterday, urgency.urgency_level,
    )

    return build_recommendation_response(
        wb, rec,
        cloud_cover_pct=satellite_data.cloud_cover_pct if satellite_data else None,
    )