
"""Cliente Google Earth Engine para obtener NDVI promedio desde Sentinel-2.

Autenticación via cuenta de servicio (GEE_SERVICE_ACCOUNT + GEE_CREDENTIALS_JSON).
Se aplica buffer negativo de 20m para evitar píxeles mixtos en bordes del campo.
"""
import json
import logging
from datetime import date, timedelta

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


def get_ndvi(polygon_geojson: dict, target_date: date) -> float | None:
    """Obtiene el NDVI promedio de Sentinel-2 para un poligono y fecha.
    
    Busca la imagen mas reciente con baja cobertura de nubes dentro de los ultimos LOOKBACK_DAYS dias anteriores a target_date
    Args:
        polygon_geojson: geometría GeoJSON (Polygon o MultiPolygon).
        target_date: fecha de referencia para buscar imágenes.

    Returns:
        NDVI promedio (float entre -1 y 1), o None si no hay imágenes disponibles.

    Raises:
        RuntimeError: si GEE falla o no se puede calcular el NDVI.
    """
    try:
        _initialize_ee()

        # Construimos la geometria con buffer negativo
        geometry = ee.Geometry(polygon_geojson).buffer(BUFFER_METERS)

        # Ventana temporal: LOOCKBACK_DAYS antes de target_date
        end_date = target_date.strftime("%Y-%m-%d")
        start_date = (target_date - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")

        # Filtramos coleccion por area, fecha y cobertura de nubes
        collection = (
            ee.ImageCollection(S2_COLLECTION)
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_COVERAGE))
            .map(_mask_s2_clouds)
            .sort("CLOUDY_PIXEL_PERCENTAGE") # La mas clara primero
        )

        count = collection.size().getInfo()
        if count == 0:
            logger.warning(
                "No hay imagenes Sentinel-2 disponibles para el periodo de %s a %s",
                start_date, end_date
            )
            return None
        
        # Tomamos la iamgen mas clara y calculamos NDVI
        image = collection.first()
        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")

        result = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=10,
            maxPixels=1e9,
        ).getInfo()

        ndvi_value = result.get("NDVI")
        if ndvi_value is None:
            logger.warning("NDVI es None para el poligono - posiblemente cubierto por nubes.")
            return None
        
        logger.info("NDVI calculado: %.4f (imagen del periodo %s - %s)", ndvi_value, start_date, end_date)
        return float(ndvi_value)
    
    except Exception as e:
        raise RuntimeError(f"Error al obtener NDVI desde GEE: {e}") from e