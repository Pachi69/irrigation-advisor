"""
Balance hídrico del suelo según FAO-56.

Calcula el déficit de agua en la zona radicular (Dr), la capacidad total
de agua disponible (TAW), la fácilmente disponible (RAW) y el coeficiente
de estrés hídrico (Ks).

Fórmula principal [Ec. 85, FAO-56]:
    Dr,i = Dr,i-1 − (Pe,i + Ii) + ETc,i

Donde:
    Dr  = déficit en zona radicular (mm)
    Pe  = precipitación efectiva (mm)
    I   = riego aplicado (mm, ya corregido por eficiencia)
    ETc = evapotranspiración del cultivo = Kc × ETo (mm)

El excedente por encima de capacidad de campo (Dr < 0) se pierde como
percolación profunda; el déficit no puede superar TAW.

Simplificaciones MVP:
    - Escorrentía (RO) = 0 (asumimos superficie plana)
    - Ascenso capilar (CR) = 0 (asumimos sin napa freática somera)

Referencia:
  Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998).
  Crop evapotranspiration – FAO Irrigation and Drainage Paper 56.
  Cap. 8 (Balance hídrico del suelo), Ec. 82–85 y Tabla 19.
"""
from __future__ import annotations

from app.models.enums import SoilType
from app.schemas.calculation import EToResult, KcResult, WaterBalanceResult

# Propiedades hidraulicas del suelo (FAOP-56 Tabla 19)
# theta_fc = contenido volumetrico a capacidad de campo (m3/m3)
# theta_wp = contenido volumetrico en punto de marchitez permanente (m3/m3)
_SOIL_PROPS: dict[SoilType, dict[str, float]] = {
    SoilType.sand:            {"theta_fc": 0.10, "theta_wp": 0.04},
    SoilType.loamy_sand:      {"theta_fc": 0.12, "theta_wp": 0.05},
    SoilType.sandy_loam:      {"theta_fc": 0.18, "theta_wp": 0.08},
    SoilType.sandy_clay_loam: {"theta_fc": 0.23, "theta_wp": 0.13},
    SoilType.loam:            {"theta_fc": 0.27, "theta_wp": 0.12},
    SoilType.silt_loam:       {"theta_fc": 0.30, "theta_wp": 0.13},
    SoilType.silt:            {"theta_fc": 0.32, "theta_wp": 0.15},
    SoilType.clay_loam:       {"theta_fc": 0.32, "theta_wp": 0.20},
    SoilType.silty_clay_loam: {"theta_fc": 0.34, "theta_wp": 0.21},
    SoilType.sandy_clay:      {"theta_fc": 0.36, "theta_wp": 0.24},
    SoilType.silty_clay:      {"theta_fc": 0.38, "theta_wp": 0.25},
    SoilType.clay:            {"theta_fc": 0.40, "theta_wp": 0.27},
}

def effective_precipitation(precipitation_mm: float) -> float:
    """Fraccion de lluvia que infiltra el suelo (mm).

    Lluvias < 2 mm se asumen completamente evaporadas (suelo arido,
    superficie caliente). Por encima, se aplica un coeficiente de 0.8
    que representa la fraccion que infiltra (el resto se pierde por
    evaporacion superficial y escurrimiento).
    """
    if precipitation_mm < 2.0:
        return 0.0
    return 0.8 * precipitation_mm

def calculate_water_balance(
    eto: EToResult,
    kc: KcResult,
    precipitation_mm: float,
    previous_deficit_mm: float,
    soil_type: SoilType,
    root_depth_m: float,
    depletion_factor_p: float,
    irrigation_mm: float = 0.0,
) -> WaterBalanceResult:
    """
    Calcula el balance hídrico del suelo para un día.

    Args:
        eto:                   Resultado de ETo (mm) — FAO-56 Penman-Monteith.
        kc:                    Resultado de Kc — dinámico o tabular.
        precipitation_mm:      Lluvia total del día (mm).
        previous_deficit_mm:   Déficit acumulado al final del día anterior (mm).
        soil_type:             Tipo de suelo del campo.
        root_depth_m:          Profundidad radicular efectiva (m).
        depletion_factor_p:    Factor de agotamiento p del cultivo [0-1].
        irrigation_mm:         Riego efectivo aplicado (mm, ya con eficiencia).

    Returns:
        WaterBalanceResult con water_deficit_mm, ks, taw_mm, raw_mm.
    """
    # propiedades hidraulicas del suelo
    soil = _SOIL_PROPS[soil_type]
    theta_fc = soil["theta_fc"]
    theta_wp = soil["theta_wp"]

    # TAW y RAW
    taw_mm = 1000 * (theta_fc - theta_wp) * root_depth_m
    raw_mm = depletion_factor_p * taw_mm

    # ETc (evapotranspiracion del cultivo)
    etc_mm = kc.kc * eto.eto_mm

    # Precipitacion efectiva
    pe_mm = effective_precipitation(precipitation_mm)

    # Balance del dia
    # Dr_i = Dr_{i-1} − (Pe + I) + ETc
    raw_deficit = previous_deficit_mm - (pe_mm + irrigation_mm) + etc_mm

    # Limitar al rango fisico
    # <0 → suelo a capacidad de campo, el exceso se pierde por percolación
    # >TAW → suelo totalmente seco
    water_deficit_mm = max(0.0, min(raw_deficit, taw_mm))

    # Coeficiente de estres hidrico Ks
    if water_deficit_mm <= raw_mm:
        ks = 1.0 #Sin estres la planta transpira al maximo
    elif water_deficit_mm >= taw_mm:
        ks = 0.0 #Estres total, la planta no puede extraer mas agua
    else:
        ks = (taw_mm - water_deficit_mm) / (taw_mm - raw_mm)

    return WaterBalanceResult(
        water_deficit_mm=water_deficit_mm,
        ks=ks,
        taw_mm=taw_mm,
        raw_mm=raw_mm
    )