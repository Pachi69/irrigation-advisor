"""
Parámetros hídricos por cultivo según FAO-56 Tabla 22.

Estos valores son defaults razonables para cultivos establecidos en Mendoza.
Si en el futuro se requiere precisión, pueden ajustarse por edad del cultivo
o medición directa.

Referencia:
  Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998).
  Crop evapotranspiration – FAO Irrigation and Drainage Paper 56.
  Tabla 22: Profundidades radiculares y factores de agotamiento p.
"""

from __future__ import annotations

from app.models.field import CropType

# root_depth_m: profundida radicular efectiva(m)
# depletion_factor_p: fraccion de TAW que puede agotarse antes del estres
CROP_WATER_PARAMS: dict[CropType, dict[str, float]] = {
    CropType.vine: {"root_depth_m": 1.5, "depletion_factor_p": 0.45},
    CropType.peach: {"root_depth_m": 1.5, "depletion_factor_p": 0.50},
    CropType.alfalfa: {"root_depth_m": 1.5, "depletion_factor_p": 0.55},
}

def get_root_depth(crop_type: CropType) -> float:
    """Profundidad radicular efectiva por defecto del cultivo (m)."""
    return CROP_WATER_PARAMS[crop_type]["root_depth_m"]

def get_depletion_factor(crop_type: CropType) -> float:
    """Factor de agotamiento p por defecto del cultivo."""
    return CROP_WATER_PARAMS[crop_type]["depletion_factor_p"]