"""Servicio de pipeline de recomendacion de riego.

Contiene la logica central reutilizada por el endpoint REST y el job automatico.
"""
from datetime import date as DateType, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.field import Field as FieldModel
from app.models.satellite_record import SatelliteRecord, SatelliteSource
from app.models.recommendation import Recommendation
from app.schemas.calculation import EToResult
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


def run_recommendation_pipeline(field: FieldModel, db: Session) -> RecommendationResponse:
    """Ejecuta el pipeline completo de recomendacion para un campo activo.

    Args:
        field: campo activo con poligono asignado.
        db:    sesion de base de datos activa.

    Returns:
        RecommendationResponse con todos los resultados del pipeline.

    Raises:
        ValueError:   si faltan variables climaticas obligatorias.
        RuntimeError: si falla la obtencion de pronostico climatico.
    """
    today = DateType.today()
    yesterday = today - timedelta(days=1)

    # Datos climaticos de ayer
    climate = get_climate_data(field.latitude, field.longitude, yesterday)
    if climate.eto_reference_mm is None:
        eto_result = calculate_eto(climate, field.latitude, yesterday, field.elevation_m)
        climate = climate.model_copy(update={"eto_reference_mm": eto_result.eto_mm})
    eto = EToResult(eto_mm=climate.eto_reference_mm)

    # NDVI mas reciente (maximo NDVI_MAX_AGE_DAYS dias)
    cutoff = today - timedelta(days=NDVI_MAX_AGE_DAYS)
    sat_record = (
        db.query(SatelliteRecord)
        .filter(SatelliteRecord.field_id == field.id, SatelliteRecord.date >= cutoff)
        .order_by(SatelliteRecord.date.desc())
        .first()
    )
    if sat_record is None and field.polygon_geojson:
        try:
            indices = get_satellite_indices(field.polygon_geojson, yesterday)
            if indices is not None:
                sat_record = SatelliteRecord(
                    field_id=field.id, date=yesterday,
                    source=SatelliteSource.sentinel2,
                    ndvi=indices.ndvi,
                    cloud_cover_pct=indices.cloud_cover_pct,
                    moisture_event_detected=False,
                )
                db.add(sat_record)
                logger.info("NDVI obtenido de GEE: %.4f", indices.ndvi)
        except RuntimeError as e:
            logger.warning("No se pudo obtener NDVI de GEE: %s. Se usara Kc tabular.", e)

    satellite_data = None
    ndvi_date = None
    if sat_record:
        satellite_data = SatelliteData(
            field_id=field.id, date=sat_record.date,
            source=sat_record.source, ndvi=sat_record.ndvi,
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
        eto=eto, kc=kc_result,
        precipitation_mm=climate.precipitation_mm,
        previous_deficit_mm=previous_deficit,
        soil_type=field.soil_type,
        root_depth_m=get_root_depth(field.crop_type),
        depletion_factor_p=get_depletion_factor(field.crop_type),
    )

    # Persistir deficit
    field.last_deficit_mm = balance.water_deficit_mm
    field.last_deficit_date = yesterday

    # Pronostico y urgencia
    forecast = get_forecast(field.latitude, field.longitude, days=3)
    urgency = calculate_urgency(balance, forecast, kc_result)

    # Upsert recomendacion
    rec = (
        db.query(Recommendation)
        .filter(Recommendation.field_id == field.id, Recommendation.date == yesterday)
        .first()
    )
    if rec is None:
        rec = Recommendation(field_id=field.id, date=yesterday)
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
    rec.taw_mm = balance.taw_mm
    rec.raw_mm = balance.raw_mm
    rec.ndvi = sat_record.ndvi if sat_record else None
    rec.ndvi_date = ndvi_date

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