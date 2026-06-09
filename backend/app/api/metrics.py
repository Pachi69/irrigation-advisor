from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.sector import Sector as SectorModel
from app.schemas.metrics import SectorMetricsResponse
from app.services.metrics import compute_sector_metrics
from app.api._helpers import owned_sector

router = APIRouter(prefix="/sectors", tags=["metrics"])


@router.get("/{sector_id}/metrics", response_model=SectorMetricsResponse)
def get_sector_metrics(
    start: date | None = Query(None, description="Inicio de la ventana (inclusive)"),
    end: date | None = Query(None, description="Fin de la ventana (inclusive)"),
    days: int = Query(90, ge=7, le=365, description="Ventana hacia atras si no se da start/end"),
    sector: SectorModel = Depends(owned_sector),
    db: Session = Depends(get_db),
):
    """Metricas de evaluacion del sector sobre una ventana de fechas."""
    end_d = end or date.today()
    start_d = start or (end_d - timedelta(days=days - 1))
    return compute_sector_metrics(sector, start_d, end_d, db)