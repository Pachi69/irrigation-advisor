"""
Cálculo del índice de urgencia de riego.

Combina el estado hídrico actual del suelo con el pronóstico climático
para determinar cuándo y cuánto regar.

Lógica:
  1. Urgencia base anclada en RAW (gatilla en Dr >= RAW = p * TAW)
  2. Piso absoluto si Ks < 0.5 (estrés severo ya en curso)
  3. Proyección del déficit a 3 días con pronóstico
  4. Ajuste por lluvia esperada ponderada por probabilidad
  5. Nivel de confianza desde fuente del Kc
"""
from __future__ import annotations

from app.models.enums import ConfidenceLevel, KcSource, UrgencyLevel
from app.schemas.calculation import KcResult, WaterBalanceResult, UrgencyResult
from app.schemas.climate import ForecastDay
from app.calculation.water_balance import effective_precipitation

# Sub-bandas de Ks para escalar la urgencia DENTRO de la zona de estres.
# El gatillo de riego es Dr >= RAW (= p·TAW) [FAO-56, Ec. 83]: por debajo de RAW
# la planta transpira al potencial (Ks=1) y no necesita riego.
_KS_MEDIUM_FLOOR = 0.75   # estres leve
_KS_HIGH_FLOOR = 0.50     # estres moderado; por debajo, severo

# Umbral de lluvia esperada (cruda, ponderada por probabilidad) en 3 dias
# para considerarla "significativa" en el texto de la recomendacion
_SIGNIFICANT_RAIN_MM = 5.0

# Ks minimo antes de declarar CRITICAL sin importar el pronostico
_KS_CRITICAL_FLOOR = 0.5

# Refill parcial: al regar, deja un colchón para la lluvia efectiva esperada
# (ponderada por probabilidad) de los próximos días, para que infiltre en vez de
# percolar. Se capa en RAW/2 para no dejar el suelo tan vacío que re-gatille el
# riego de inmediato ni roce el estrés si la lluvia pronosticada no se concreta.
_RAIN_BUFFER_HORIZON = 3
_RAIN_BUFFER_CAP_FRACTION = 0.5

# Orden de niveles para subir/bajar urgencia
_LEVELS = [UrgencyLevel.low, UrgencyLevel.medium, UrgencyLevel.high, UrgencyLevel.critical]

def _upgrade(level: UrgencyLevel, steps: int = 1) -> UrgencyLevel:
    return _LEVELS[min(_LEVELS.index(level) + steps, len(_LEVELS) - 1)]

def _downgrade(level: UrgencyLevel, steps: int = 1) -> UrgencyLevel:
    return _LEVELS[max(_LEVELS.index(level) - steps, 0)]


def _urgency_from_deficit(deficit_mm: float, raw_mm: float, taw_mm: float) -> UrgencyLevel:
    """Urgencia base anclada en RAW (FAO-56).

    Dr < RAW             -> low      (sin estres, no se recomienda regar)
    Dr >= RAW, Ks alto   -> medium   (estres leve, ya conviene regar)
    Ks moderado          -> high
    Ks < 0.5             -> critical (estres severo)
    """
    if deficit_mm < raw_mm:
        return UrgencyLevel.low
    ks = (taw_mm - deficit_mm) / (taw_mm - raw_mm) if taw_mm > raw_mm else 0.0
    if ks >= _KS_MEDIUM_FLOOR:
        return UrgencyLevel.medium
    if ks >= _KS_HIGH_FLOOR:
        return UrgencyLevel.high
    return UrgencyLevel.critical


def _project_deficit(
    current_deficit_mm: float,
    taw_mm: float,
    kc_value: float,
    forecast: list[ForecastDay],
    days: int = 3,
) -> float:
    """Estima el deficit en N dias aplicando ETc y lluvia ponderada del pronostico.
    La lluvia se multiplica por su probabilidad para reflejar la incertidumbre."""
    projected = current_deficit_mm
    for day in forecast[:days]:
        etc = kc_value * day.eto_reference_mm
        pe_weighted = (
            effective_precipitation(day.precipitation_mm)
            * (day.precipitation_probability_pct / 100.0)
        )
        projected = max(0.0, min(projected - pe_weighted + etc, taw_mm))
    return projected

def _rain_buffer(forecast: list[ForecastDay], raw_mm: float) -> float:
    """Colchón (mm) a dejar bajo capacidad de campo al regar (refill parcial).

    Reserva lugar para la lluvia efectiva esperada en los próximos
    `_RAIN_BUFFER_HORIZON` días, ponderada por su probabilidad, de modo que esa
    lluvia infiltre en vez de percolar. Se acota a `_RAIN_BUFFER_CAP_FRACTION`·RAW
    (RAW/2) para no dejar el suelo tan seco que re-gatille el riego de inmediato
    ni roce el estrés si la lluvia pronosticada no se concreta.

    Sin lluvia pronosticada el colchón es 0 -> repone a capacidad de campo,
    idéntico al comportamiento sin refill parcial.
    """
    expected = sum(
        effective_precipitation(day.precipitation_mm) * (day.precipitation_probability_pct / 100.0)
        for day in forecast[:_RAIN_BUFFER_HORIZON]
    )
    return min(expected, _RAIN_BUFFER_CAP_FRACTION * raw_mm)


def calculate_urgency(
    water_balance: WaterBalanceResult,
    forecast: list[ForecastDay],
    kc: KcResult,
) -> UrgencyResult:
    """
    Calcula el índice de urgencia de riego y la cantidad recomendada.

    Args:
        water_balance: Resultado del balance hídrico del día.
        forecast:      Pronóstico de los próximos días (mínimo 3 recomendado).
        kc:            Coeficiente de cultivo del día.

    Returns:
        UrgencyResult con urgency_level, recommended_irrigation_mm, reason y confidence.
    """
    deficit = water_balance.water_deficit_mm
    taw = water_balance.taw_mm
    ks = water_balance.ks
    raw = water_balance.raw_mm

    # Urgencia base anclada en RAW
    urgency = _urgency_from_deficit(deficit, raw, taw)

    # Piso absoluto: estres severo ya en curso
    if ks < _KS_CRITICAL_FLOOR:
        urgency = UrgencyLevel.critical

    # Proyeccion a 3 dias 
    projected_deficit = _project_deficit(deficit, taw, kc.kc, forecast, days=3)
    projected_urgency = _urgency_from_deficit(projected_deficit, raw, taw)

    if _LEVELS.index(projected_urgency) > _LEVELS.index(urgency):
        urgency = _upgrade(urgency)

    # Ajuste por lluvia esperada ponderada por probabilidad
    weighted_rain_3d = sum(
        effective_precipitation(day.precipitation_mm) * (day.precipitation_probability_pct / 100.0)
        for day in forecast[:3]
    )
    max_prob_3d = max(
        (day.precipitation_probability_pct for day in forecast[:3]), default=0.0
    )

    # Lluvia esperada para el TEXTO: lluvia cruda ponderada SOLO por probabilidad.
    # No usa precipitacion efectiva (ese descuento es para el balance hidrico).
    expected_rain_3d = sum(
        day.precipitation_mm * (day.precipitation_probability_pct / 100.0)
        for day in forecast[:3]
    )

    # Bajar urgencia solo si hay alta probabilidad de lluvia suficiente
    # Si Ks < piso critico, no bajamos aunque llueva
    if urgency == UrgencyLevel.critical and ks >= _KS_CRITICAL_FLOOR:
        if weighted_rain_3d > 0.6 * deficit and max_prob_3d >= 80:
            urgency = _downgrade(urgency)
    elif urgency == UrgencyLevel.high:
        if weighted_rain_3d > 0.5 * deficit and max_prob_3d >= 70:
            urgency = _downgrade(urgency)
    elif urgency == UrgencyLevel.medium:
        if weighted_rain_3d > deficit and max_prob_3d >= 70:
            urgency = _downgrade(urgency)

    # Cantidad recomendada (refill parcial): repone el déficit dejando un colchón
    # para la lluvia esperada. Excepciones: si no hay urgencia no riega; bajo
    # estrés severo repone a FC completo (no apuesta a la lluvia con la planta ya
    # sufriendo). Sin pronóstico de lluvia el colchón es 0 y repone a FC.
    if urgency == UrgencyLevel.low:
        recommended_mm = 0.0
    elif ks < _KS_CRITICAL_FLOOR:
        recommended_mm = deficit
    else:
        recommended_mm = max(0.0, deficit - _rain_buffer(forecast, raw))

    # Confianza desde fuente del Kc
    confidence = kc.kc_confidence

    deficit_ratio = deficit / taw if taw > 0 else 0.0
    projected_ratio = projected_deficit / taw if taw > 0 else 0.0

    # Razon legible
    reason = _build_reason(deficit_ratio, ks, expected_rain_3d, max_prob_3d, projected_ratio)

    return UrgencyResult(
        urgency_level=urgency,
        recommended_irrigation_mm=round(recommended_mm, 1),
        reason=reason,
        confidence=confidence
    )


def urgency_from_balance(water_balance: WaterBalanceResult, kc: KcResult) -> UrgencyResult:
    """Urgencia de un dia sin pronóstico."""
    deficit = water_balance.water_deficit_mm
    taw = water_balance.taw_mm
    raw = water_balance.raw_mm
    ks = water_balance.ks

    urgency = _urgency_from_deficit(deficit, raw, taw)
    if ks < _KS_CRITICAL_FLOOR:
        urgency = UrgencyLevel.critical
    
    recommended_mm = deficit if urgency != UrgencyLevel.low else 0.0

    confidence = kc.kc_confidence

    deficit_ratio = deficit / taw if taw > 0 else 0.0
    pct = round(deficit_ratio * 100)
    reason = f"Deficit hidrico: {pct}% de la capacidad disponible."
    if ks < 1.0:
        reason += f" Estres hidrico en curso (Ks={ks:.2f})."

    return UrgencyResult(
        urgency_level=urgency,
        recommended_irrigation_mm=round(recommended_mm, 1),
        reason=reason,
        confidence=confidence
    )


def _build_reason(
    deficit_ratio: float,
    ks: float,
    expected_rain_3d: float,
    max_prob_3d: float,
    projected_ratio: float,
) -> str:
    """Genera texto explicativo de la recomendación en lenguaje natural."""
    parts = []

    pct = round(deficit_ratio * 100)
    parts.append(f"Déficit hidrico actual: {pct}% de la capacidad disponible")

    if ks < 1.0:
        parts.append(f"Estres hidrico en curso (Ks={ks:.2f}).")

    if expected_rain_3d > _SIGNIFICANT_RAIN_MM:
        parts.append(
            f"Lluvia esperada próximos 3 días: {expected_rain_3d:.1f} mm "
            f"(probabilidad máx. {max_prob_3d:.0f}%)."
        )
    else:
        parts.append("Sin lluvia significativa prevista en los próximos 3 días.")

    proj_pct = round(projected_ratio * 100)
    if proj_pct > pct + 10:
        parts.append(f"Proyección a 3 días: el déficit subirá al {proj_pct}%.")

    return " ".join(parts)