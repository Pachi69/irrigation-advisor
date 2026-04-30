
"""Cliente Google Earth Engine para obtener NDVI promedio desde Sentinel-2.

Autenticación via cuenta de servicio (GEE_SERVICE_ACCOUNT + GEE_CREDENTIALS_JSON).
Se aplica buffer negativo de 20m para evitar píxeles mixtos en bordes del campo.
"""
import json
import logging
from datetime import date, timedelta
from dataclasses import dataclass

import ee

from app.config import settings

logger = logging.getLogger(__name__)

# Coleccion Sentinel-2 Surface Reflectance armonizada
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"

# Buffer negativo en metros para evitar pixeles mixtos en los bordes
BUFFER_METERS = -20

# Dias hacia atras a buscar una imagen clara (sin nubes)
LOOKBACK_DAYS = 30

# Umbral maximo de cobertura de nubes por imagen (%)
MAX_CLOUD_COVERAGE = 20

def _initialize_ee() -> None:
    """Inicializa Earth Engine con la cuenta de servicio si no esta inicializado"""
    if not ee.data._credentials:
        credentials = ee.ServiceAccountCredentials(
            email=settings.gee_service_account,
            key_data=settings.gee_credentials_json,
        )
        ee.Initialize(credentials, project=settings.gee_project_id)


def _mask_s2_clouds(image: ee.Image) -> ee.Image:
    """Enmascara pixeles nublados usando la banda SCL de Sentinel-2 SR."""
    scl = image.select("SCL")
    # SCL: 4=vegetation, 5=bare soil 6=water, 7=unclassified
    # Excluimos: 3=cloud shadow, 8=cloud medium, 9= cloud high, 10=thin cirrus
    clear_mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(clear_mask)
    

@dataclass
class SatelliteIndices:
    """Indices espectrales calculados desde Sentinel-2"""
    ndvi: float
    cloud_cover_pct: float
    image_date: date


def get_satellite_indices(polygon_geojson: dict, target_date: date) -> SatelliteIndices | None:
    """
    Obtiene NDVI promedio desde Sentinel-2 via GEE.

    NDVI = (B8 - B4) / (B8 + B4)

    Args:
        polygon_geojson: geometría GeoJSON del campo.
        target_date: fecha de referencia (busca hacia atrás LOOKBACK_DAYS días).

    Returns:
        SatelliteIndices o None si no hay imágenes disponibles.

    Raises:
        RuntimeError: si GEE falla.
    """
    try:
        _initialize_ee()

        geojson = polygon_geojson.get("geometry", polygon_geojson) if polygon_geojson.get("type") == "Feature" else polygon_geojson
        geometry = ee.Geometry(geojson).buffer(BUFFER_METERS)
        end_date = target_date.strftime("%Y-%m-%d")
        start_date = (target_date - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")

        collection = (
            ee.ImageCollection(S2_COLLECTION)
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_COVERAGE))
            .map(_mask_s2_clouds)
            .sort("system:time_start", False)
        )

        if collection.size().getInfo() == 0:
            logger.warning("No hay imágenes Sentinel-2 para %s a %s", start_date, end_date)
            return None

        image = collection.first()
        cloud_cover = float(image.get("CLOUDY_PIXEL_PERCENTAGE").getInfo() or 0.0)

        image_date_str = ee.Date(image.get("system:time_start")).format("YYYY-MM-dd").getInfo()
        image_date = date.fromisoformat(image_date_str)

        ndvi_band = image.normalizedDifference(["B8", "B4"]).rename("NDVI")

        result = (
            ndvi_band
            .reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=10,
                maxPixels=1e9,
            )
            .getInfo()
        )

        ndvi_val = result.get("NDVI")
        if ndvi_val is None:
            logger.warning("NDVI es None para el polígono - posiblemente cubierto por nubes.")
            return None

        indices = SatelliteIndices(
            ndvi=float(ndvi_val),
            cloud_cover_pct=cloud_cover,
            image_date=image_date
        )
        logger.info("NDVI desde GEE: %.4f (imagen del %s)", indices.ndvi, indices.image_date)
        return indices

    except Exception as e:
        raise RuntimeError(f"Error al obtener índices satelitales desde GEE: {e}") from e