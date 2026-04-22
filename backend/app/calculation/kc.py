"""
Cálculo del coeficiente de cultivo (Kc) dinámico a partir de NDVI (FAO-56 + literatura).

Estrategia:
  1. Si hay NDVI disponible → Kc dinámico por cobertura fraccionada  [fuente: s2_dynamic]
  2. Si no hay NDVI         → Kc tabular FAO-56 según etapa fenológica [fuente: tabular]

Referencias:
  Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998).
  Crop evapotranspiration – Guidelines for computing crop water requirements.
  FAO Irrigation and Drainage Paper 56. FAO, Rome.
  https://www.fao.org/3/x0490e/x0490e.pdf

  Glenn, E.P., Neale, C.M.U., Hunsaker, D.J., Nagler, P.L. (2011).
  Vegetation index-based crop coefficients to estimate evapotranspiration
  by remote sensing in agricultural and natural ecosystems.
  Hydrological Processes, 25(26), 4050–4062.
  https://doi.org/10.1002/hyp.8392
"""

from __future__ import annotations

from datetime import date
from dataclasses import dataclass

from app.models.field import CropType
from app.models.recommendation import KcSource, PhenologicalStage
from app.schemas.calculation import KcResult
from app.schemas.satellite import SatelliteData


@dataclass(frozen=True)
class _CropKcParams:
    """Parametros Kc tabular FAO-56 y limites NDVI por cultivo."""
    kc_ini: float    # Kc etapa inicial
    kc_mid: float    # Kc etapa media (máximo)
    kc_end: float    # Kc etapa final
    l_ini: int       # Duración etapa inicial (días)
    l_dev: int       # Duración etapa desarrollo (días)
    l_mid: int       # Duración etapa media (días)
    l_late: int      # Duración etapa tardía (días)
    ndvi_soil: float = 0.15   # NDVI suelo desnudo
    ndvi_full: float = 0.85   # NDVI cobertura completa


_KC_PARAMS: dict[CropType, _CropKcParams] = {
    CropType.vine: _CropKcParams(
        kc_ini=0.30, kc_mid=0.70, kc_end=0.45,
        l_ini=30, l_dev=60, l_mid=40, l_late=80,
    ),
    CropType.peach: _CropKcParams(
        kc_ini=0.45, kc_mid=1.15, kc_end=0.75,
        l_ini=20, l_dev=70, l_mid=120, l_late=60,
    ),
    CropType.alfalfa: _CropKcParams(
        kc_ini=0.40, kc_mid=1.05, kc_end=0.90,
        l_ini=10, l_dev=30, l_mid=35, l_late=10,
    ),
}

def _stage_from_days(days: int, p: _CropKcParams) -> PhenologicalStage:
    """Determina la etapa fenologica segun dias desde siembra/brotacion."""
    if days < p.l_ini:
        return PhenologicalStage.initial
    if days < p.l_ini + p.l_dev:
        return PhenologicalStage.development
    if days < p.l_ini + p.l_dev + p.l_mid:
        return PhenologicalStage.mid
    return PhenologicalStage.late


def _kc_tabular(days: int, p: _CropKcParams) -> tuple[float, PhenologicalStage]:
    """Kc tabular FAO-56 con interpolacion lineal entre etapas"""
    stage = _stage_from_days(days, p)
    
    if days < p.l_ini:
        kc = p.kc_ini
    elif days < p.l_ini + p.l_dev:
        frac = (days - p.l_ini) / p.l_dev
        kc = p.kc_ini + frac * (p.kc_mid - p.kc_ini)
    elif days < p.l_ini + p.l_dev + p.l_mid:
        kc = p.kc_mid
    else:
        frac = min((days - p.l_ini - p.l_dev - p.l_mid) / p.l_late, 1.0)
        kc = p.kc_mid + frac * (p.kc_end - p.kc_mid)

    return kc, stage


def _kc_from_ndvi(ndvi: float, p: _CropKcParams) -> tuple[float, PhenologicalStage]:
    """
    Kc dinamico desde NDVI usando cobertura fraccionada.
    
    fc = (NDVI - NDVI_soil) / (NDVI_full - NDVI_soil) -> fraccion de cobertura vegetal
    Kc = Kc_ini + (Kc_mid - Kc_ini) * fc
    Referencia: Glenn et al. (2011); adaptado FAO-56.
    """
    fc = (ndvi - p.ndvi_soil) / (p.ndvi_full - p.ndvi_soil)
    fc = max(0.0, min(1.0, fc))

    kc = p.kc_ini + (p.kc_mid - p.kc_ini) * fc
    
    # Etapa fenologica estimada desde cobertura fraccionada
    if fc < 0.2:
        stage = PhenologicalStage.initial
    elif fc < 0.5:
        stage = PhenologicalStage.development
    else:
        stage = PhenologicalStage.mid

    return kc, stage


def calculate_kc(
    crop_type: CropType,
    planting_date: date,
    current_date: date,
    satellite_data: SatelliteData | None,
) -> KcResult:
    """Calcula el coeficiente de cultivo (Kc) para la fecha indicada.
    Prioriza NDVI satelital si esta disponible; si no, usa Kc tabular FAO-56.
    Args:
        crop_type:      Tipo de cultivo del campo.
        planting_date:  Fecha de siembra o brotación.
        current_date:   Fecha para la que se calcula el Kc.
        satellite_data: Datos satelitales recientes (puede ser None).

    Returns:
        KcResult con kc, source y phenological_stage.

    Raises:
        ValueError: si el crop_type no tiene parámetros definidos."""
    params = _KC_PARAMS.get(crop_type)
    if params is None:
        raise ValueError(f"No hay parametros Kc definidos para el cultivo: {crop_type}")
    
    days = max((current_date - planting_date).days, 0)

    # Estrategia 1: Kc dinamico desde NDVI Satelital
    if satellite_data is not None and satellite_data.ndvi is not None:
        kc, stage = _kc_from_ndvi(satellite_data.ndvi, params)
        return KcResult(kc=kc, source=KcSource.s2_dynamic, phenological_stage=stage)
    
    # Estrategia 2: Kc tabular FAO-56
    kc, stage = _kc_tabular(days, params)
    return KcResult(kc=kc, source=KcSource.tabular, phenological_stage=stage)