"""Servicio de balance hidrico diario: calculo y persistencia de DailyWaterBalance."""
from datetime import date as DateType

import logging

from sqlalchemy.orm import Session

from app.models.field import Field as FieldModel
from app.models.daily_water_balance import DailyWaterBalance
from app.schemas.calculation import EToResult, KcResult, WaterBalanceResult
from app.schemas.climate import ClimateData
from app.schemas.satellite import SatelliteData
from app.ingestion.climate import get_climate_data
from app.calculation.eto import calculate_eto
from app.calculation.kc import calculate_kc
from app.calculation.water_balance import calculate_water_balance
from app.calculation.crop_params import get_root_depth, get_depletion_factor
from app.services.satellite import get_satellite_data_for_date

logger = logging.getLogger(__name__)


def compute_balance_from_data(
    field: FieldModel,
    target_date: DateType,
    *,
    climate: ClimateData,
    satellite_data: SatelliteData | None,
    ndvi_date: DateType | None,
    previous_deficit_mm: float,
) -> tuple[ClimateData, EToResult, SatelliteData | None, DateType | None, KcResult, WaterBalanceResult]:
    """Calcula ETo, Kc y balance hidrico para un dia a partir de datos ya traidos.

    Actualiza field.last_deficit_mm y field.last_deficit_date.
    """
    if climate.eto_reference_mm is None:
        eto_result = calculate_eto(climate, field.latitude, target_date, field.elevation_m)
        climate = climate.model_copy(update={"eto_reference_mm": eto_result.eto_mm})
    eto = EToResult(eto_mm=climate.eto_reference_mm)

    kc_result = calculate_kc(
        crop_type=field.crop_type,
        current_date=target_date,
        satellite_data=satellite_data,
    )

    balance = calculate_water_balance(
        eto=eto,
        kc=kc_result,
        precipitation_mm=climate.precipitation_mm,
        previous_deficit_mm=previous_deficit_mm,
        soil_type=field.soil_type,
        root_depth_m=get_root_depth(field.crop_type),
        depletion_factor_p=get_depletion_factor(field.crop_type),
    )

    field.last_deficit_mm = balance.water_deficit_mm
    field.last_deficit_date = target_date

    return climate, eto, satellite_data, ndvi_date, kc_result, balance

def compute_balance_for_day(
    field: FieldModel, target_date: DateType, db: Session
) -> tuple[ClimateData, EToResult, SatelliteData | None, DateType | None, KcResult, WaterBalanceResult]:
    """Calcula el balance para una fecha trayendo clima y satelite por su cuenta.

    Usado por el pipeline en vivo (dia de ayer). El backfill usa la version batch.

    Actualiza field.last_deficit_mm y field.last_deficit_date.
    """
    climate = get_climate_data(field.latitude, field.longitude, target_date)
    satellite_data, ndvi_date = get_satellite_data_for_date(field, target_date, db)

    last_wb = (
        db.query(DailyWaterBalance)
        .filter(
            DailyWaterBalance.field_id == field.id,
            DailyWaterBalance.date < target_date,
        )
        .order_by(DailyWaterBalance.date.desc())
        .first()
    )
    previous_deficit = last_wb.water_deficit_mm if last_wb else (field.last_deficit_mm or 0.0)

    return compute_balance_from_data(
        field, target_date,
        climate=climate,
        satellite_data=satellite_data,
        ndvi_date=ndvi_date,
        previous_deficit_mm=previous_deficit,
    )


def save_water_balance(
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
) -> DailyWaterBalance:
    """Crea o actualiza DailyWaterBalance para un campo en una fecha."""
    wb = (
        db.query(DailyWaterBalance)
        .filter(DailyWaterBalance.field_id == field.id, DailyWaterBalance.date == target_date)
        .first()
    )
    if wb is None:
        wb = DailyWaterBalance(field_id=field.id, date=target_date)
        db.add(wb)

    wb.eto_mm = eto.eto_mm
    wb.kc = kc_result.kc
    wb.kc_source = kc_result.source
    wb.etc_mm = eto.eto_mm * kc_result.kc
    wb.water_deficit_mm = balance.water_deficit_mm
    wb.ks = balance.ks
    wb.phenological_stage = kc_result.phenological_stage
    wb.precipitation_mm = climate.precipitation_mm
    wb.taw_mm = balance.taw_mm
    wb.raw_mm = balance.raw_mm
    wb.ndvi = satellite_data.ndvi if satellite_data else None
    wb.ndvi_date = ndvi_date
    db.flush()

    return wb