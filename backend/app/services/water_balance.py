"""Servicio de balance hidrico diario: calculo y persistencia de DailyWaterBalance."""
from datetime import date as DateType

import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sector import Sector as SectorModel
from app.models.daily_water_balance import DailyWaterBalance
from app.models.irrigation_confirmation import IrrigationConfirmation
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


def confirmed_irrigation_mm(sector_id: int, target_date: DateType, db: Session) -> float:
    """Suma del riego confirmado por el productor para un campo en una fecha (mm)"""
    total = (
        db.query(func.coalesce(func.sum(IrrigationConfirmation.applied_irrigation_mm), 0.0))
        .filter(
            IrrigationConfirmation.sector_id == sector_id,
            IrrigationConfirmation.irrigation_date == target_date
        )
        .scalar()
    )
    return float(total or 0.0)

def confirmed_irrigation_by_range(sector_id: int, start: DateType, end: DateType, db: Session) -> dict[DateType, float]:
    """Riego confirmado por fecha en un rango (para el backfill, evita n+1)"""
    rows = (
        db.query(
            IrrigationConfirmation.irrigation_date,
            func.sum(IrrigationConfirmation.applied_irrigation_mm),
        )
        .filter(
            IrrigationConfirmation.sector_id == sector_id,
            IrrigationConfirmation.irrigation_date >= start,
            IrrigationConfirmation.irrigation_date <= end,
        )
        .group_by(IrrigationConfirmation.irrigation_date)
        .all()
    )
    return {d: float(s) for d,s in rows}

def compute_balance_from_data(
    sector: SectorModel,
    target_date: DateType,
    *,
    climate: ClimateData,
    satellite_data: SatelliteData | None,
    ndvi_date: DateType | None,
    previous_deficit_mm: float,
    irrigation_mm: float = 0.0,
) -> tuple[ClimateData, EToResult, SatelliteData | None, DateType | None, KcResult, WaterBalanceResult]:
    """Calcula ETo, Kc y balance hidrico para un dia a partir de datos ya traidos."""
    field = sector.field

    eto_mm = climate.eto_reference_mm
    if eto_mm is None:
        eto_result = calculate_eto(climate, field.latitude, target_date, field.elevation_m)
        eto_mm = eto_result.eto_mm
        climate = climate.model_copy(update={"eto_reference_mm": eto_mm})
    eto = EToResult(eto_mm=eto_mm)

    kc_result = calculate_kc(
        crop_type=sector.crop_type,
        current_date=target_date,
        satellite_data=satellite_data,
        hail_net_type=sector.hail_net_type,
    )

    balance = calculate_water_balance(
        eto=eto,
        kc=kc_result,
        precipitation_mm=climate.precipitation_mm,
        previous_deficit_mm=previous_deficit_mm,
        soil_type=field.soil_type,
        root_depth_m=get_root_depth(sector.crop_type),
        depletion_factor_p=get_depletion_factor(sector.crop_type),
        irrigation_mm=irrigation_mm,
    )

    sector.last_deficit_mm = balance.water_deficit_mm
    sector.last_deficit_date = target_date

    return climate, eto, satellite_data, ndvi_date, kc_result, balance

def compute_balance_for_day(
    sector: SectorModel, target_date: DateType, db: Session
) -> tuple[ClimateData, EToResult, SatelliteData | None, DateType | None, KcResult, WaterBalanceResult]:
    """Calcula el balance para una fecha trayendo clima y satelite por su cuenta."""
    field = sector.field
    climate = get_climate_data(field.latitude, field.longitude, target_date)
    satellite_data, ndvi_date = get_satellite_data_for_date(sector, target_date, db)

    last_wb = (
        db.query(DailyWaterBalance)
        .filter(
            DailyWaterBalance.sector_id == sector.id,
            DailyWaterBalance.date < target_date,
        )
        .order_by(DailyWaterBalance.date.desc())
        .first()
    )
    previous_deficit = last_wb.water_deficit_mm if last_wb else (sector.last_deficit_mm or 0.0)
    irrigation_mm = confirmed_irrigation_mm(sector.id, target_date, db)

    return compute_balance_from_data(
        sector, target_date,
        climate=climate,
        satellite_data=satellite_data,
        ndvi_date=ndvi_date,
        previous_deficit_mm=previous_deficit,
        irrigation_mm=irrigation_mm,
    )


def save_water_balance(
    sector: SectorModel,
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
        .filter(DailyWaterBalance.sector_id == sector.id, DailyWaterBalance.date == target_date)
        .first()
    )
    if wb is None:
        wb = DailyWaterBalance(sector_id=sector.id, date=target_date)
        db.add(wb)

    wb.eto_mm = eto.eto_mm
    wb.kc = kc_result.kc
    wb.kc_source = kc_result.source
    wb.etc_mm = eto.eto_mm * kc_result.kc
    wb.water_deficit_mm = balance.water_deficit_mm
    wb.ks = balance.ks
    wb.phenological_stage = kc_result.phenological_stage
    wb.precipitation_mm = climate.precipitation_mm
    wb.temp_max_c = climate.temp_max_c
    wb.temp_min_c = climate.temp_min_c
    wb.temp_mean_c = climate.temp_mean_c
    wb.humidity_pct = climate.humidity_pct
    wb.wind_speed_ms = climate.wind_speed_10m
    wb.solar_radiation_mj = climate.solar_radiation_mj
    wb.pressure_kpa = climate.pressure_kpa
    wb.taw_mm = balance.taw_mm
    wb.raw_mm = balance.raw_mm
    wb.ndvi = satellite_data.ndvi if satellite_data else None
    wb.ndvi_date = ndvi_date
    db.flush()

    return wb