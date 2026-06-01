"""Conversion entre lamina de riego (mm) y unidades operativas (volumen, tiempo).

La recomendacion se calcula en lamina NETA (mm), el agua que infiltra y repone el deficit.
El productor opera en TIEMPO de riego y le sirve el VOLUMEN (m3), ambos en BRUTO: el agua
que el sistema debe entregar, mayor que la neta por las perdidas de aplicacion (escurrimiento,
percolacion). El factor de correlacion es la eficiencia, derivada del metodo de riego.

1mm sobre 1ha = 10 m3 = 10.000 L.
"""
from app.models.enums import IrrigationType


# Eficiencia de aplicacion por metodo de riego (FAO-56).
_IRRIGATION_EFFICIENCY = {
    IrrigationType.superficial: 0.6,
    IrrigationType.aspersion: 0.85, # microaspersion/aspersion localizada (FAO-56: aspersion 85-90%)
}


def efficiency_for(irrigation_type: IrrigationType) -> float:
    """Eficiencia de aplicacion del metodo de riego."""
    return _IRRIGATION_EFFICIENCY[irrigation_type]

def mm_to_volume_m3(lamina_mm: float, area_ha: float | None, eff: float) -> float | None:
    """Lamina neta (mm) -> volumen bruto (m3) que el sistema debe entregar"""
    if not area_ha or eff <= 0:
        return None
    return lamina_mm * area_ha * 10 / eff

def mm_to_time_min(lamina_mm: float, flow_ls_ha: float | None, eff: float) -> float | None:
    """Lámina neta (mm) → tiempo de riego (min). La superficie se cancela."""
    if not flow_ls_ha or eff <= 0:
        return None
    return lamina_mm * 10000 / (flow_ls_ha * eff) / 60

def time_min_to_mm(time_min: float | None, flow_ls_ha: float | None, eff: float) -> float:
    """Tiempo de riego bruto (min) -> lamina neta (mm) que infiltró. Inversa de mm_to_time_min."""
    if not time_min or not flow_ls_ha:
        return 0.0
    return time_min * 60 * flow_ls_ha * eff / 10000

def volume_m3_to_mm(volume_m3: float, area_ha: float | None, eff: float) -> float:
    """Volumen bruto aplicado (m3) -> lamina neta (mm) que infiltro. Inversa de mm_to_volume_m3"""
    if not area_ha or eff <= 0:
        return 0.0
    return volume_m3 * eff / (area_ha * 10)
