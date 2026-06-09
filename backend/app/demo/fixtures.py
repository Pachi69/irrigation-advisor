"""Fixture en memoria para la seccion DEMO (sin tocar la BD).

Replica la identidad y geometria del sector Malbec real como un
objeto plano, para correr el pipeline de recomendacion sobre una
fecha de verano sin depender de filas en la BD ni del flujo de aprobacion
de campos.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.models.enums import CropType, HailNetType, IrrigationType, SoilType


#Poligono real del sector Malbec, copiado en memoria
MALBEC_POLYGON: dict = {
    "type": "Polygon",
      "coordinates": [[
        [-68.389152, -34.551705],
        [-68.389571, -34.552607],
        [-68.38272, -34.554931],
        [-68.38228, -34.554025],
        [-68.389152, -34.551705],
    ]],
}

@dataclass(frozen=True)
class DemoSector:
    """Sector de demo: los mismos campos que necesita el motor, sin SQLAlchemy."""
    name: str
    variety: str
    crop_type: CropType
    soil_type: SoilType
    irrigation_type: IrrigationType
    hail_net_type: HailNetType
    area_ha: float
    flow_rate_ls_ha: float | None
    latitude: float
    longitude: float
    elevation_m: float | None
    polygon_geojson: dict

#identidad copiada del Malbec real
DEMO_SECTOR = DemoSector(
    name="Malbec — demo de verano",
    variety="Malbec",
    crop_type=CropType.vine,
    soil_type=SoilType.sandy_loam,
    irrigation_type=IrrigationType.aspersion,
    hail_net_type=HailNetType.open,   # malla abierta real -> Kc desde NDVI, confianza media
    area_ha=7.3485,
    flow_rate_ls_ha=None,             # el Malbec real no tiene caudal cargado
    latitude=-34.55374286111111,
    longitude=-68.38564780555555,
    elevation_m=735.0,
    polygon_geojson=MALBEC_POLYGON,
)

# --- Caso demo (fechas preset) ---
# Ancla "tanque lleno": temporal saturante real del 5-9 ene 2026 (~51 mm).
# Arrancamos el roll en la lluvia para que cualquier seed inicial se "lave".
DEMO_ANCHOR_DATE = date(2026, 1, 5)
# Fecha objetivo: imagen S2 limpia con buen NDVI (~0.42) y deficit intermedio.
DEMO_TARGET_DATE = date(2026, 2, 3)