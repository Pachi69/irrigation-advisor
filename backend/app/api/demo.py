"""API de la seccion DEMO (sin DB ni auth): corre el pipeline sobre una fecha de verano."""
import logging

from fastapi import APIRouter, HTTPException, Response, status

from app.schemas.demo import DemoSnapshot
from app.services.demo import compute_demo_snapshot, get_demo_thumbnail

router = APIRouter(prefix="/demo", tags=["demo"])
logger = logging.getLogger(__name__)


@router.get("/snapshot", response_model=DemoSnapshot)
def demo_snapshot(refresh: bool = False):
    """Snapshot del caso demo. ?refresh=true fuerza recalculo (vuelve a pegarle a GEE)."""
    try:
        return compute_demo_snapshot(force=refresh)
    except Exception as e:
        logger.exception("Error al calcular el snapshot de demo")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo calcular la demo: {e}",
        )


@router.get("/satellite-image")
def demo_satellite_image():
    """Thumbnail NDVI (PNG) de la fecha objetivo de la demo."""
    png = get_demo_thumbnail()
    if not png:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagen de demo no disponible")
    return Response(content=png, media_type="image/png")