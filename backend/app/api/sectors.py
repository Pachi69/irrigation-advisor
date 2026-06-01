"""API del recurso sector: CRUD + lecturas de estado (imagen satelital, charts)"""
from datetime import date as date_type, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.field import Field as FieldModel
from app.models.sector import Sector as SectorModel
from app.models.satellite_record import SatelliteRecord
from app.models.daily_water_balance import DailyWaterBalance
from app.models.recommendation import Recommendation
from app.schemas.field import FieldPublic
from app.schemas.sector import SectorCreate, SectorPublic, SectorUpdate, SectorChartData, DeficitPoint, NdviPoint, LastRecommendationSummary
from app.services.sector import create_sector, update_field_geo
from app.api._geo import setup_field_geo
from app.api._helpers import owned_field, owned_sector
from app.calculation.crop_params import get_depletion_factor

router = APIRouter(tags=["sectors"])

_HISTORY_POINTS = 10


def _build_last_recommendation(db: Session, sector_id: int) -> LastRecommendationSummary | None:
    """Última recomendación accionable del sector con historial de déficit para sparklines."""
    history_rows = (
        db.query(Recommendation, DailyWaterBalance)
        .join(DailyWaterBalance, Recommendation.water_balance_id == DailyWaterBalance.id)
        .filter(
            DailyWaterBalance.sector_id == sector_id,
            Recommendation.taw_mm.is_not(None),
            Recommendation.taw_mm > 0,
        )
        .order_by(DailyWaterBalance.date.desc())
        .limit(_HISTORY_POINTS)
        .all()
    )
    if not history_rows:
        return None

    rec, wb = history_rows[0]
    deficit_history = [
        round((r.water_deficit_mm / r.taw_mm) * 100, 1)
        for r, _ in reversed(history_rows)
    ]
    return LastRecommendationSummary(
        date=wb.date,
        urgency=rec.urgency,
        recommended_irrigation_mm=rec.recommended_irrigation_mm,
        time_min=rec.time_min,
        volume_m3=rec.volume_m3,
        deficit_pct=round((wb.water_deficit_mm / wb.taw_mm) * 100, 1),
        deficit_history=deficit_history,
    )

def enrich_sector(sector: SectorModel, db: Session) -> SectorPublic:
    """SectorPublic con su ultima recomendacion embebida"""
    public = SectorPublic.model_validate(sector)
    public.last_recommendation = _build_last_recommendation(db, sector.id)
    return public

def build_field_public(field: FieldModel, db: Session, schema: type[FieldPublic] = FieldPublic) -> FieldPublic:
    """FieldPublic (o subclase) con sus sectores enriquecidos"""
    public = schema.model_validate(field)
    public.sectors = [enrich_sector(s, db) for s in field.sectors]
    return public


@router.post("/fields/{field_id}/sectors", response_model=SectorPublic, status_code=status.HTTP_201_CREATED)
def create_field_sector(
    data: SectorCreate,
    field: FieldModel = Depends(owned_field),
    db: Session = Depends(get_db),
):
    sector = create_sector(field, data, db)
    if sector.polygon_geojson:
        update_field_geo(field, db)
    db.commit()
    db.refresh(sector)
    return enrich_sector(sector, db)


@router.get("/fields/{field_id}/sectors", response_model=List[SectorPublic])
def list_field_sectors(field: FieldModel = Depends(owned_field), db: Session = Depends(get_db)):
    return [enrich_sector(s, db) for s in field.sectors]


@router.get("/sectors/{sector_id}", response_model=SectorPublic)
def get_sector(sector: SectorModel = Depends(owned_sector), db: Session = Depends(get_db)):
    return enrich_sector(sector, db)


@router.patch("/sectors/{sector_id}", response_model=SectorPublic)
def update_sector(data: SectorUpdate, sector: SectorModel = Depends(owned_sector), db: Session = Depends(get_db)):
    for attr, value in data.model_dump(exclude_unset=True).items():
        setattr(sector, attr, value)

    if data.polygon_geojson is not None:
        _, _, sector.area_ha = setup_field_geo(data.polygon_geojson)
        update_field_geo(sector.field, db)

    db.commit()
    db.refresh(sector)
    return enrich_sector(sector, db)


@router.delete("/sectors/{sector_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sector(sector: SectorModel = Depends(owned_sector), db: Session = Depends(get_db)):
    db.delete(sector)
    db.commit()


@router.get("/sectors/{sector_id}/satellite-image")
def get_sector_satellite_image(sector: SectorModel = Depends(owned_sector), db: Session = Depends(get_db)):
    record = (
        db.query(SatelliteRecord)
        .filter(
            SatelliteRecord.sector_id == sector.id,
            SatelliteRecord.thumbnail_png.is_not(None),
        )
        .order_by(SatelliteRecord.date.desc())
        .first()
    )
    if not record or not record.thumbnail_png:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagen satelital no encontrada")
    return Response(content=record.thumbnail_png, media_type="image/png")


@router.get("/sectors/{sector_id}/chart", response_model=SectorChartData)
def get_sector_chart(sector: SectorModel = Depends(owned_sector), db: Session = Depends(get_db)):
    cutoff = date_type.today() - timedelta(days=90)
    balances = (
        db.query(DailyWaterBalance)
        .filter(
            DailyWaterBalance.sector_id == sector.id,
            DailyWaterBalance.date >= cutoff,
            DailyWaterBalance.taw_mm.is_not(None),
        )
        .order_by(DailyWaterBalance.date.asc())
        .all()
    )
    satellite_records = (
        db.query(SatelliteRecord)
        .filter(SatelliteRecord.sector_id == sector.id, SatelliteRecord.date >= cutoff)
        .order_by(SatelliteRecord.date.asc())
        .all()
    )
    return SectorChartData(
        deficit=[DeficitPoint(date=b.date, pct=round(min(100, (b.water_deficit_mm / b.taw_mm) * 100), 1))
                 for b in balances if b.taw_mm and b.taw_mm > 0
                ],
        ndvi=[NdviPoint(date=r.date, value=round(r.ndvi, 4))
              for r in satellite_records if r.ndvi is not None
            ],
        raw_threshold_pct=round(get_depletion_factor(sector.crop_type) * 100, 1),
    )