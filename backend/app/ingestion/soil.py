"""Consulta SoilGrids 2.0 (ISRIC) para determinar el tipo de suelo desde coordenadas.
API REST gratuita (CC-BY 4.0), sin credenciales requeridas.

Referencia: Poggio et al. (2021). SoilGrids 2.0: producing soil information for the
globe with quantified spatial uncertainty. SOIL, 7, 217-240.
https://doi.org/10.5194/soil-7-217-2021
"""
import logging
import httpx

from app.models.enums import SoilType

logger = logging.getLogger(__name__)

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
_TIMEOUT = 15 # segundos


def _classify_usda(sand: float, silt: float, clay: float) -> str:
    """Clasifica textura de suelo segun triangulo USDA de porcentajes."""
    if clay >= 40 and silt < 40 and sand <= 45:
        return "clay"
    if clay >= 40 and silt >= 40:
        return "silty_clay"
    if clay >= 35 and sand > 45:
        return "sandy_clay"
    if clay >= 27 and clay < 40 and sand <= 20:
        return "silty_clay_loam"
    if clay >= 27 and clay < 40 and sand > 20 and sand <= 45:
        return "clay_loam"
    if clay >= 20 and sand > 45:
        return "sandy_clay_loam"
    if clay < 27 and silt >= 50 and silt < 80:
        return "silt_loam"
    if silt >= 80 and clay < 12:
        return "silt"
    if clay >= 7 and clay < 27 and silt >= 28 and sand < 52:
        return "loam"
    if sand >= 85 and clay <= 10:
        return "sand"
    if sand >= 70 and clay <= 15:
        return "loamy_sand"
    if sand >= 52:
        return "sandy_loam"
    return "loam"

_USDA_TO_SOIL_TYPE: dict[str, SoilType] = {
    "sand":            SoilType.sand,
    "loamy_sand":      SoilType.loamy_sand,
    "sandy_loam":      SoilType.sandy_loam,
    "sandy_clay_loam": SoilType.sandy_clay_loam,
    "loam":            SoilType.loam,
    "silt_loam":       SoilType.silt_loam,
    "silt":            SoilType.silt,
    "clay_loam":       SoilType.clay_loam,
    "silty_clay_loam": SoilType.silty_clay_loam,
    "sandy_clay":      SoilType.sandy_clay,
    "silty_clay":      SoilType.silty_clay,
    "clay":            SoilType.clay,
}


def get_soil_type_from_coords(lat: float, lon: float) -> SoilType | None:
    """Consulta SoilGrids 2.0 REST API y retorna el tipo de suelo FAO-56.
    
    Args:
        lat: Latitud decimal del centroide del campo.
        lon: Longitud decimal del centroide del campo.

    Returns:
        SoilType: una de las 12 clases texturales USDA/FAO-56, o None si la API no esta disponible.
    """
    try: 
        params = {
            "lat": lat,
            "lon": lon,
            "property": ["clay", "silt", "sand"],
            "depth": "0-5cm",
            "value": "mean",
        }
        with httpx.Client(timeout=_TIMEOUT) as client:
            r = client.get(SOILGRIDS_URL, params=params)
            r.raise_for_status()
        
        layers = {
            layer["name"]: layer["depths"][0]["values"]["mean"]
            for layer in r.json()["properties"]["layers"]
            if layer["depths"][0]['values']['mean'] is not None
        }

        if not all(k in layers for k in ("clay", "silt", "sand")):
            logger.warning("SoilGrids: fracciones incompletas para (%.4f, %.4f)", lat, lon)
            return None
        
        clay = layers["clay"] * 0.1 # g/kg -> %
        silt = layers["silt"] * 0.1
        sand = layers["sand"] * 0.1

        # Control de calidad: fracciones deben sumar ~100%
        total = clay + silt + sand
        if total < 80:
            logger.warning(
                "SoilGrids: fracciones invalidas (total=%.1f%%) para (%.4f, %.4f) - se descarta", total, lat, lon
            )
            return None
        
        usda_class = _classify_usda(sand, silt, clay)
        soil_type = _USDA_TO_SOIL_TYPE[usda_class]

        logger.info(
            "SoilGrids (%.4f, %.4f): sand=%.1f%% silt=%.1f%% clay=%.1f%% → %s → %s",
            lat, lon, sand, silt, clay, usda_class, soil_type.value
        )
        return soil_type
    
    except Exception as e:
        logger.warning("SoilGrids no disponible: %s. Se usara tipo de suelo manual", e)
        return None

        