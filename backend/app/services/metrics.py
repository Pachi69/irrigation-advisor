"""Servicio de metricas / evaluacion por sector.

Agrega el balance hidrico diario, las recomendaciones y las confirmaciones de
una ventana de fechas en KPIs de periodo y una serie semanal. Solo lectura.

El contrafactico de ahorro es la "reposicion ciega de ETc": cuanto se habria
regado reponiendo la demanda del cultivo (ETc) todos los dias, sin aprovechar
la lluvia ni la reserva de agua del suelo. El agua evitada por el sistema es la
diferencia contra lo recomendado.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date as DateType, timedelta

from sqlalchemy.orm import Session, joinedload

from app.models.sector import Sector as SectorModel
from app.models.daily_water_balance import DailyWaterBalance
from app.models.irrigation_confirmation import IrrigationConfirmation
from app.models.enums import KcSource, UrgencyLevel
from app.calculation.irrigation import efficiency_for, mm_to_volume_m3
from app.calculation.water_balance import effective_precipitation
from app.schemas.metrics import (
    SectorMetricsResponse, WaterSummary, StressSummary, AdherenceSummary,
    UrgencyDistribution, SatelliteQuality, ClimateSummary, WeeklyWaterMetrics,
)

def _week_start(d: DateType) -> DateType:
    """Lunes de la semana ISO que contiene d."""
    return d - timedelta(days=d.weekday())

def compute_sector_metrics(sector: SectorModel, start: DateType, end: DateType, db: Session) -> SectorMetricsResponse:
    eff = efficiency_for(sector.irrigation_type)
    area = sector.area_ha

    def to_m3(mm: float) -> float | None:
        v = mm_to_volume_m3(round(mm, 1), area, eff)
        return round(v, 1) if v is not None else None
    
    balances = (
        db.query(DailyWaterBalance)
        .filter(
            DailyWaterBalance.sector_id == sector.id,
            DailyWaterBalance.date >= start,
            DailyWaterBalance.date <= end,
        )
        .options(joinedload(DailyWaterBalance.recommendation))
        .order_by(DailyWaterBalance.date.asc())
        .all()
    )

    # Confirmaciones por fecha de riego dentro de la ventana (agua aplicada fisica)
    confirmations = (
        db.query(IrrigationConfirmation)
        .filter(
            IrrigationConfirmation.sector_id == sector.id,
            IrrigationConfirmation.irrigation_date >= start,
            IrrigationConfirmation.irrigation_date <= end,
        )
        .all()
    )

    # Acumuladores de periodo
    sum_eto = sum_etc = sum_rain = sum_eff_rain = sum_recommended = 0.0
    days_eval = stress_days = severe_days = days_above_raw = 0
    sum_ks = 0.0
    ks_count = 0
    min_ks: float | None = None
    sum_deficit = sum_deficit_pct = 0.0
    max_deficit: float | None = None
    urg_counts = {u: 0 for u in UrgencyLevel}
    s2_days = tab_days = ndvi_days = 0
    sum_ndvi = 0.0

    weekly = defaultdict(lambda: {
        "eto": 0.0, "etc": 0.0, "eff_rain": 0.0, "recommended": 0.0,
        "applied": 0.0, "days": 0, "ks_sum": 0.0, "ks_n": 0, "stress": 0,
    })

    actionable_ids: list[int] = []
    for b in balances:
        days_eval += 1
        sum_eto += b.eto_mm
        sum_etc += b.etc_mm
        sum_rain += b.precipitation_mm
        eff_rain = effective_precipitation(b.precipitation_mm)
        sum_eff_rain += eff_rain

        if b.ks is not None:
            sum_ks += b.ks
            ks_count += 1
            if min_ks is None or b.ks < min_ks:
                min_ks = b.ks
            if b.ks < 1.0:
                stress_days += 1
            if b.ks < 0.5:
                severe_days += 1

        sum_deficit += b.water_deficit_mm
        if b.taw_mm:
            sum_deficit_pct += min(1.0, max(0.0, b.water_deficit_mm / b.taw_mm))
        if max_deficit is None or b.water_deficit_mm > max_deficit:
            max_deficit = b.water_deficit_mm
        if b.raw_mm is not None and b.water_deficit_mm > b.raw_mm:
            days_above_raw += 1

        if b.kc_source == KcSource.s2_dynamic:
            s2_days += 1
        else:
            tab_days += 1
        if b.ndvi is not None:
            ndvi_days += 1
            sum_ndvi += b.ndvi

        rec = b.recommendation
        if rec:
            urg_counts[rec.urgency] += 1
            if rec.recommended_irrigation_mm > 0:
                actionable_ids.append(rec.id)
        
        wk = weekly[_week_start(b.date)]
        wk["eto"] += b.eto_mm
        wk["etc"] += b.etc_mm
        wk["eff_rain"] += eff_rain
        wk["days"] += 1
        if b.ks is not None:
            wk["ks_sum"] += b.ks
            wk["ks_n"] += 1
            if b.ks < 1.0:
                wk["stress"] += 1
    
    # agua aplicada (fisica) total + semanal
    sum_applied = 0.0
    for c in confirmations:
        sum_applied += c.applied_irrigation_mm
        weekly[_week_start(c.irrigation_date)]["applied"] += c.applied_irrigation_mm

    # adherencia: de las recomendaciones accionables de la ventana, cuantas se confirmaron
    confirmed_ids: set[int] = set()
    if actionable_ids:
        rows = (
            db.query(IrrigationConfirmation.recommendation_id)
            .filter(IrrigationConfirmation.recommendation_id.in_(actionable_ids))
            .all()
        )
        confirmed_ids = {r[0] for r in rows}
    actionable = len(actionable_ids)
    confirmed = len(confirmed_ids)

    # water summary (demanda neta IRn vs contrafactico ETc-ciego)
    # IRn = ma(0, ETc - lluvia efectiva): el agua de riego que el cultivo necesito neta de la lluvia
    # No es la suma de recomendaciones diarias (esa suma cuenta el mismo deficit parado muchas veces)
    baseline_mm = sum_etc
    net_requirement_mm = max(0.0, sum_etc - sum_eff_rain)
    avoided_mm = baseline_mm - net_requirement_mm
    avoided_pct = (avoided_mm / baseline_mm * 100) if baseline_mm > 0 else None

    water = WaterSummary(
        net_requirement_mm=round(net_requirement_mm, 1),
        net_requirement_m3=to_m3(net_requirement_mm),
        applied_mm=round(sum_applied, 1),
        applied_m3=to_m3(sum_applied),
        baseline_etc_mm=round(baseline_mm, 1),
        baseline_etc_m3=to_m3(baseline_mm),
        avoided_mm=round(avoided_mm, 1),
        avoided_m3=to_m3(avoided_mm),
        avoided_pct=round(avoided_pct, 1) if avoided_pct is not None else None,
    )

    stress = StressSummary(
        days_evaluated=days_eval,
        stress_days=stress_days,
        stress_days_pct=round(stress_days / days_eval * 100, 1) if days_eval else 0.0,
        severe_stress_days=severe_days,
        severe_stress_days_pct=round(severe_days / days_eval * 100, 1) if days_eval else 0.0,
        avg_ks=round(sum_ks / ks_count, 2) if ks_count else None,
        min_ks=round(min_ks, 2) if min_ks is not None else None,
        avg_deficit_mm=round(sum_deficit / days_eval, 1) if days_eval else None,
        avg_deficit_pct=round(sum_deficit_pct / days_eval * 100, 1) if days_eval else None,
        max_deficit_mm=round(max_deficit, 1) if max_deficit is not None else None,
        days_above_raw=days_above_raw,
    )

    adherence = AdherenceSummary(
        actionable=actionable,
        confirmed=confirmed,
        pending=actionable - confirmed,
        adherence_pct=round(confirmed / actionable * 100, 1) if actionable else None,
    )

    urgency = UrgencyDistribution(
        low=urg_counts[UrgencyLevel.low],
        medium=urg_counts[UrgencyLevel.medium],
        high=urg_counts[UrgencyLevel.high],
        critical=urg_counts[UrgencyLevel.critical],
    )

    satellite =  SatelliteQuality(
        days_evaluated=days_eval,
        s2_dynamic_days=s2_days,
        tabular_days=tab_days,
        s2_dynamic_pct=round(s2_days / days_eval * 100, 1) if days_eval else 0.0,
        ndvi_days=ndvi_days,
        avg_ndvi=round(sum_ndvi / ndvi_days, 3) if ndvi_days else None
    )

    climate = ClimateSummary(
        eto_mm=round(sum_eto, 1),
        etc_mm=round(sum_etc, 1),
        rain_mm=round(sum_rain, 1),
        effective_rain_mm=round(sum_eff_rain, 1),
    )

    weekly_list = []
    for ws in sorted(weekly.keys()):
        w = weekly[ws]
        etc_w = w["etc"]
        eff_rain_w = w["eff_rain"]
        net_req_w = max(0.0, etc_w - eff_rain_w)
        weekly_list.append(WeeklyWaterMetrics(
            week_start=ws,
            week_end=min(ws + timedelta(days=6), end),
            days=w["days"],
            eto_mm=round(w["eto"], 1),
            etc_mm=round(etc_w, 1),
            effective_rain_mm=round(eff_rain_w, 1),
            net_requirement_mm=round(net_req_w, 1),
            net_requirement_m3=to_m3(net_req_w),
            applied_mm=round(w["applied"], 1),
            applied_m3=to_m3(w["applied"]),
            baseline_etc_mm=round(etc_w, 1),
            avoided_mm=round(etc_w - net_req_w, 1),
            avoided_m3=to_m3(etc_w - net_req_w),
            avg_ks=round(w["ks_sum"] / w["ks_n"], 2) if w["ks_n"] else None,
            stress_days=w["stress"],
        ))

    return SectorMetricsResponse(
        sector_id=sector.id,
        start_date=start,
        end_date=end,
        water=water,
        stress=stress,
        adherence=adherence,
        urgency=urgency,
        satellite=satellite,
        climate=climate,
        weekly=weekly_list
    )