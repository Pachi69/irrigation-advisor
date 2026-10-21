"""
Balance hídrico del suelo según FAO-56.

Calcula el déficit de agua en la zona radicular (Dr), la capacidad total
de agua disponible (TAW), la fácilmente disponible (RAW) y el coeficiente
de estrés hídrico (Ks).

Fórmula principal [Ec. 85, FAO-56]:
    Dr,i = Dr,i-1 − (Pe,i + Ii) + ETc_adj,i

Donde:
    Dr      = déficit en zona radicular (mm)
    Pe      = precipitación efectiva (mm)
    I       = riego aplicado (mm, ya corregido por eficiencia)
    ETc_adj = ET ajustada por estrés = Ks × Kc × ETo (mm) [Ec. 81]
    Con Dr ≤ RAW es Ks=1, así que ETc_adj = Kc × ETo (condición estándar).

El excedente por encima de capacidad de campo (Dr < 0) se pierde como
percolación profunda; el déficit no puede superar TAW.

Simplificaciones MVP:
    - Escorrentía (RO) = 0 (FAO-56 Cap. 7: las lluvias leves escurren poco o nada)
    - Ascenso capilar (CR) = 0 (asumimos sin napa freática somera)

Referencia:
  Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998).
  Crop evapotranspiration – FAO Irrigation and Drainage Paper 56.
  Cap. 8 (Balance hídrico del suelo), Ec. 82–85 y Tabla 19.
"""
from __future__ import annotations

from app.models.enums import SoilType
from app.schemas.calculation import EToResult, KcResult, WaterBalanceResult

# Propiedades hidraulicas del suelo por textura USDA (Saxton & Rawls, 2006)
# theta_fc = contenido volumetrico a capacidad de campo (m3/m3)
# theta_wp = contenido volumetrico en punto de marchitez permanente (m3/m3)
_SOIL_PROPS: dict[SoilType, dict[str, float]] = {
    SoilType.sand:            {"theta_fc": 0.10, "theta_wp": 0.05},
    SoilType.loamy_sand:      {"theta_fc": 0.12, "theta_wp": 0.05},
    SoilType.sandy_loam:      {"theta_fc": 0.18, "theta_wp": 0.08},
    SoilType.sandy_clay_loam: {"theta_fc": 0.27, "theta_wp": 0.17},
    SoilType.loam:            {"theta_fc": 0.28, "theta_wp": 0.14},
    SoilType.silt_loam:       {"theta_fc": 0.31, "theta_wp": 0.11},
    SoilType.silt:            {"theta_fc": 0.30, "theta_wp": 0.06},
    SoilType.clay_loam:       {"theta_fc": 0.36, "theta_wp": 0.22},
    SoilType.silty_clay_loam: {"theta_fc": 0.38, "theta_wp": 0.22},
    SoilType.sandy_clay:      {"theta_fc": 0.36, "theta_wp": 0.25},
    SoilType.silty_clay:      {"theta_fc": 0.41, "theta_wp": 0.27},
    SoilType.clay:            {"theta_fc": 0.42, "theta_wp": 0.30},
}

def effective_precipitation(precipitation_mm: float, eto_mm: float) -> float:
    """Precipitacion efectiva del dia (mm) [FAO-56, Cap. 8].

    La lluvia diaria menor a 0.2 × ETo normalmente se evapora por completo
    y no entra al balance; el Kc unico ya incluye esa evaporacion del suelo.
    Por encima del umbral, toda la lluvia entra al suelo (escorrentia RO = 0,
    FAO-56 Cap. 7).
    """
    if precipitation_mm < 0.2 * eto_mm:
        return 0.0
    return precipitation_mm

def _water_stress_coefficient(deficit_mm: float, raw_mm: float, taw_mm: float) -> float:
    """Coeficiente de estres hidrico Ks [Ec. 84, FAO-56].
    
    Ks = 1                          si Dr <= RAW        (sin estres)
    Ks = (TAW - Dr) / (TAW - RAW)   si RAW < Dr < TAW   (estres lineal)
    Ks = 0                          si Dr >= TAW        (estres total)
    """
    if deficit_mm <= raw_mm:
        return 1.0
    if deficit_mm >= taw_mm:
        return 0.0
    return (taw_mm - deficit_mm) / (taw_mm - raw_mm)

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

    # ETc potencial (condiciones estandar) = Kc × ETo  [Caps. 5-7, FAO-56]
    etc_pot = kc.kc * eto.eto_mm

    # Precipitacion efectiva
    pe_mm = effective_precipitation(precipitation_mm, eto.eto_mm)

    # Ks de INICIO de dia, segun el deficit con que arranca el dia.
    # FAO-56 Cap. 8: si el suelo ya esta por debajo de RAW, la planta no
    # transpira al potencial y la ET real baja a ETc_adj = Ks × ETc [Ec. 81].
    # Se usa el Ks de inicio (deficit previo) para evitar circularidad: el
    # agua que la planta puede extraer hoy depende del estado con que arranca.
    # Con Dr_prev <= RAW es Ks=1, asi que ETc_adj = ETc (operacion normal).
    ks_start = _water_stress_coefficient(previous_deficit_mm, raw_mm, taw_mm)
    etc_adj = ks_start * etc_pot

    # Balance del dia
    # Dr_i = Dr_{i-1} − (Pe + I) + ETc_adj
    raw_deficit = previous_deficit_mm - (pe_mm + irrigation_mm) + etc_adj

    # Percolacion profunda: si el agua que entro (Pe + I) supera el deficit previo
    # mas la ETc_adj, el suelo pasa capacidad de campo y el excedente drena por debajo
    # de la zona radicular y se pierde
    deep_percolation_mm = max(0.0, -raw_deficit)

    # Limitar al rango fisico
    # <0 → suelo a capacidad de campo, el exceso se pierde por percolación
    # >TAW → suelo totalmente seco
    water_deficit_mm = max(0.0, min(raw_deficit, taw_mm))

    # Ks de FIN de dia (estado reportado; gobierna la urgencia)
    ks = _water_stress_coefficient(water_deficit_mm, raw_mm, taw_mm)

    return WaterBalanceResult(
        water_deficit_mm=water_deficit_mm,
        ks=ks,
        taw_mm=taw_mm,
        raw_mm=raw_mm,
        deep_percolation_mm=deep_percolation_mm
    )