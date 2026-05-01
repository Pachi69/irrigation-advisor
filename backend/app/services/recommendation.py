"""Servicio de pipeline de recomendacion de riego.

Contiene la logica central reutilizada por el endpoint REST y el job automatico.
"""
from datetime import date as DateType, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.field import Field as FieldModel
from app.models.satellite_record import SatelliteRecord, SatelliteSource
from app.models.recommendation import Recommendation, UrgencyLevel, ConfidenceLevel
from app.schemas.calculation import EToResult, KcResult, WaterBalanceResult
from app.schemas.climate import ClimateData
from app.schemas.recommendation import RecommendationResponse
from app.schemas.satellite import SatelliteData
from app.ingestion.climate import get_climate_data, get_forecast
from app.ingestion.satellite import get_satellite_indices
from app.calculation.eto import calculate_eto
from app.calculation.kc import calculate_kc
from app.calculation.water_balance import calculate_water_balance
from app.calculation.crop_params import get_root_depth, get_depletion_factor
from app.calculation.urgency import calculate_urgency
from app.services.push import send_push_to_user

logger = logging.getLogger(__name__)
NDVI_MAX_AGE_DAYS = 15


def _get_satellite_data_for_date(
    field: FieldModel, target_date: DateType, db: Session
) -> tuple[SatelliteData | None, DateType | None]:
    """Devuelve el NDVI vigente a una fecha (mas reciente con fecha <= target_date,
    dentro de los ultimos NDVI_MAX_AGE_DAYS dias)."""
    cutoff = target_date - timedelta(days=NDVI_MAX_AGE_DAYS)
    sat_record = (
        db.query(SatelliteRecord)
        .filter(
            SatelliteRecord.field_id == field.id,
            SatelliteRecord.date <= target_date,
            SatelliteRecord.date >= cutoff,
        )
        .order_by(SatelliteRecord.date.desc())
        .first()
    )
    if sat_record is None:
        return None, None
    return (
        SatelliteData(
            field_id=field.id, date=sat_record.date,
            source=sat_record.source, ndvi=sat_record.ndvi,
        ),
        sat_record.date,
    )


def _compute_balance_for_day(
    field: FieldModel, target_date: DateType, db: Session
) -> tuple[ClimateData, EToResult, SatelliteData | None, DateType | None, KcResult, WaterBalanceResult]:
    """Calcula clima, ETo, Kc y balance hidrico para una fecha.

    Actualiza field.last_deficit_mm y field.last_deficit_date.
    """
    climate = get_climate_data(field.latitude, field.longitude, target_date)
    if climate.eto_reference_mm is None:
        eto_result = calculate_eto(climate, field.latitude, target_date, field.elevation_m)
        climate = climate.model_copy(update={"eto_reference_mm": eto_result.eto_mm})
    eto = EToResult(eto_mm=climate.eto_reference_mm)

    satellite_data, ndvi_date = _get_satellite_data_for_date(field, target_date, db)

    kc_result = calculate_kc(
        crop_type=field.crop_type,
        planting_date=field.planting_date,
        current_date=target_date,
        satellite_data=satellite_data,
    )

    last_rec = (
        db.query(Recommendation)
        .filter(
            Recommendation.field_id == field.id,
            Recommendation.date < target_date,
            Recommendation.water_deficit_mm.is_not(None),
        )
        .order_by(Recommendation.date.desc())
        .first()
    )
    previous_deficit = last_rec.water_deficit_mm if last_rec else 0.0
    balance = calculate_water_balance(
        eto=eto, 
        kc=kc_result,
        precipitation_mm=climate.precipitation_mm,
        previous_deficit_mm=previous_deficit,
        soil_type=field.soil_type,
        root_depth_m=get_root_depth(field.crop_type),
        depletion_factor_p=get_depletion_factor(field.crop_type),
    )

    field.last_deficit_mm = balance.water_deficit_mm
    field.last_deficit_date = target_date

    return climate, eto, satellite_data, ndvi_date, kc_result, balance


def _upsert_recommendation(
    field: FieldModel,
    target_date: DateType,
    db: Session,
    *,
    climate: ClimateData,
    eto: EToResult,
    kc_result: KcResult,
    balance: WaterBalanceResult,
    satellite_data: SatelliteData | None,
    ndvi_date: DateType | None,
    urgency_level: UrgencyLevel,
    recommended_irrigation_mm: float,
    reason: str,
    confidence: ConfidenceLevel,
) -> Recommendation:
    """Crea o actualiza la Recommendation para un campo en una fecha."""
    rec = (
        db.query(Recommendation)
        .filter(Recommendation.field_id == field.id, Recommendation.date == target_date)
        .first()
    )
    if rec is None:
        rec = Recommendation(field_id=field.id, date=target_date)
        db.add(rec)

    rec.eto_mm = eto.eto_mm
    rec.kc = kc_result.kc
    rec.kc_source = kc_result.source
    rec.etc_mm = eto.eto_mm * kc_result.kc
    rec.water_deficit_mm = balance.water_deficit_mm
    rec.ks = balance.ks
    rec.phenological_stage = kc_result.phenological_stage
    rec.recommended_irrigation_mm = recommended_irrigation_mm
    rec.urgency = urgency_level
    rec.reason = reason
    rec.precipitation_mm = climate.precipitation_mm
    rec.confidence = confidence
    rec.taw_mm = balance.taw_mm
    rec.raw_mm = balance.raw_mm
    rec.ndvi = satellite_data.ndvi if satellite_data else None
    rec.ndvi_date = ndvi_date
    return rec


def _save_retroactive_day(field: FieldModel, target_date: DateType, db: Session) -> None:
    """Calcula balance hidrico para una fecha pasada y guarda Recommendation retroactiva.

    Usado para rellenar dias faltantes entre la ultima recomendacion guardada y ayer,
    manteniendo la continuidad del deficit acumulado.
    """
    climate, eto, satellite_data, ndvi_date, kc_result, balance = _compute_balance_for_day(
        field, target_date, db
    )
    _upsert_recommendation(
        field, target_date, db,
        climate=climate, eto=eto, kc_result=kc_result, balance=balance,
        satellite_data=satellite_data, ndvi_date=ndvi_date,
        urgency_level=UrgencyLevel.low,
        recommended_irrigation_mm=0.0,
        reason="Recalculado retroactivamente (backfill)",
        confidence=ConfidenceLevel.low,
    )
    db.flush()
    logger.info("Backfill: dia %s, deficit %.2f mm", target_date, balance.water_deficit_mm)


def _fetch_latest_s2_if_available(field: FieldModel, today: DateType, db: Session) -> None:
    """Consulta GEE para la imagen S2 mas reciente y la persiste si no esta duplicada."""
    if not field.polygon_geojson:
        return
    try:
        new_indices = get_satellite_indices(field.polygon_geojson, today)
        if new_indices is None:
            return
        existing = (
            db.query(SatelliteRecord)
            .filter(
                SatelliteRecord.field_id == field.id,
                SatelliteRecord.date == new_indices.image_date,
            )
            .first()
        )
        if existing is None:
            db.add(SatelliteRecord(
                field_id=field.id,
                date=new_indices.image_date,
                source=SatelliteSource.sentinel2,
                ndvi=new_indices.ndvi,
                cloud_cover_pct=new_indices.cloud_cover_pct,
                moisture_event_detected=False,
            ))
            db.flush()
            logger.info(
                "Nueva imagen S2 persistida: fecha %s, NDVI %.4f",
                new_indices.image_date, new_indices.ndvi,
            )
    except RuntimeError as e:
        logger.warning(
            "No se pudo obtener NDVI de GEE: %s. Se usara registro existente o Kc tabular.", e,
        )


def run_recommendation_pipeline(field: FieldModel, db: Session) -> RecommendationResponse:
    """Ejecuta el pipeline completo de recomendacion para un campo activo.

    Args:
        field: campo activo con poligono asignado.
        db: sesion de base de datos activa.

    Returns:
        RecommendationResponse con todos los resultados del pipeline.

    Raises:
        ValueError: si faltan variables climaticas obligatorias.
        RuntimeError: si falla la obtencion de pronostico climatico.
    """
    today = DateType.today()
    yesterday = today - timedelta(days=1)

    # Backfill: rellenar dias faltantes entre last_deficit_date y ayer
    if field.last_deficit_date is not None:
        gap_date = field.last_deficit_date + timedelta(days=1)
        while gap_date < yesterday:
            try:
                _save_retroactive_day(field, gap_date, db)
            except Exception as e:
                logger.error("Error en backfill dia %s campo %d: %s", gap_date, field.id, e)
                break
            gap_date += timedelta(days=1)

    # Intenta obtener la imagen S2 mas reciente disponible
    _fetch_latest_s2_if_available(field, today, db)

    # Calcular balance hidrico de ayer
    climate, eto, satellite_data, ndvi_date, kc_result, balance = _compute_balance_for_day(
        field, yesterday, db
    )

    # Pronostico y urgencia (solo aplican al pipeline en vivo)
    forecast = get_forecast(field.latitude, field.longitude, days=3)
    urgency = calculate_urgency(balance, forecast, kc_result)

    # Persistir recomendacion completa
    _upsert_recommendation(
        field, yesterday, db,
        climate=climate, eto=eto, kc_result=kc_result, balance=balance,
        satellite_data=satellite_data, ndvi_date=ndvi_date,
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

    # Notificacion push al productor
    try:
        send_push_to_user(
            user_id=field.user_id,
            title="Recomendacion de riego",
            body=f"{urgency.reason[:80]}..." if len(urgency.reason) > 80 else urgency.reason,
            db=db,
        )
    except Exception as e:
        logger.warning("Error al enviar notificacion push: %s", e)

    return RecommendationResponse(
        field_id=field.id,
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