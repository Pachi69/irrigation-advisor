"""
Cálculo del índice de urgencia de riego.

Combina el estado hídrico actual del suelo con el pronóstico climático
para determinar cuándo y cuánto regar.

Lógica:
  1. Urgencia base desde déficit relativo (Dr / TAW)
  2. Piso absoluto si Ks < 0.5 (estrés severo ya en curso)
  3. Proyección del déficit a 3 días con pronóstico
  4. Ajuste por lluvia esperada ponderada por probabilidad
  5. Nivel de confianza desde fuente del Kc
"""
from __future__ import annotations

from app.models.recommendation import ConfidenceLevel, KcSource, UrgencyLevel
from app.schemas.calculation import KcResult, WaterBalanceResult, UrgencyResult
from app.schemas.climate import ForecastDay

# Umbrales de deficit relativo (Dr / TAW) para urgencia base
_THRESHOLDS = {
    "low_to_medium": 0.35,
    "medium_to_high": 0.55,
    "high_to_critical": 0.75,
}

# Ks minimo antes de declarar CRITICAL sin importar el pronostico
_KS_CRITICAL_FLOOR = 0.5

# Orden de niveles para subir/bajar urgencia
_LEVELS = [UrgencyLevel.low, UrgencyLevel.medium, UrgencyLevel.high, UrgencyLevel.critical]

def _upgrade(level: UrgencyLevel, steps: int = 1) -> UrgencyLevel:
    return _LEVELS[min(_LEVELS.index(level) + steps, len(_LEVELS) - 1)]

def _downgrade(level: UrgencyLevel, steps: int = 1) -> UrgencyLevel:
    return _LEVELS[max(_LEVELS.index(level) - steps, 0)]


def _urgency_from_ratio(ratio: float) -> UrgencyLevel:
    """Urgencia base desde deficit relativo Dr/TAW"""
    if ratio < _THRESHOLDS["low_to_medium"]:
        return UrgencyLevel.low
    elif ratio < _THRESHOLDS["medium_to_high"]:
        return UrgencyLevel.medium
    elif ratio < _THRESHOLDS["high_to_critical"]:
        return UrgencyLevel.high
    return UrgencyLevel.critical


def _effective_precipitation(precipitation_mm: float) -> float:
    """Fraccion de lluvia que infiltra (FAO: P<5mm → 0; P≥5mm → 0.8P − 2)"""
    if precipitation_mm < 5.0:
        return 0.0
    return 0.8 * precipitation_mm - 2.0


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
            _effective_precipitation(day.precipitation_mm)
            * (day.precipitation_probability_pct / 100.0)
        )
        projected = max(0.0, min(projected - pe_weighted + etc, taw_mm))
    return projected


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

    # Urgencia base desde deficit relativo
    deficit_ratio = deficit / taw if taw > 0 else 0.0
    urgency = _urgency_from_ratio(deficit_ratio)

    # Piso absoluto: estres severo ya en curso
    if ks < _KS_CRITICAL_FLOOR:
        urgency = UrgencyLevel.critical

    # Proyeccion a 3 dias 
    projected_deficit = _project_deficit(deficit, taw, kc.kc, forecast, days=3)
    projected_ratio = projected_deficit / taw if taw > 0 else 0.0
    projected_urgency = _urgency_from_ratio(projected_ratio)

    if _LEVELS.index(projected_urgency) > _LEVELS.index(urgency):
        urgency = _upgrade(urgency)

    # Ajuste por lluvia esperada ponderada por probabilidad
    weighted_rain_3d = sum(
        _effective_precipitation(day.precipitation_mm) * (day.precipitation_probability_pct / 100.0)
        for day in forecast[:3]
    )
    max_prob_3d = max(
        (day.precipitation_probability_pct for day in forecast[:3]), default=0.0
    )

    # Bjar urgencia solo si hay alta probabilidad de lluvia suficiente
    # Si Ks < piso critico, no bajamos aunque llueva: la planta ya esta sufriendo
    if urgency == UrgencyLevel.critical and ks >= _KS_CRITICAL_FLOOR:
        if weighted_rain_3d > 0.6 and max_prob_3d >= 80:
            urgency = _downgrade(urgency)
    elif urgency == UrgencyLevel.high:
        if weighted_rain_3d > 0.5 * deficit and max_prob_3d >= 70:
            urgency = _downgrade(urgency)
    elif urgency == UrgencyLevel.medium:
        if weighted_rain_3d > deficit and max_prob_3d >= 70:
            urgency = _downgrade(urgency)

    # Cantidad recomendada
    recommended_mm = deficit if urgency != UrgencyLevel.low else 0.0

    # Confianza desde fuente del Kc
    confidence = (
        ConfidenceLevel.high
        if kc.source == KcSource.s2_dynamic
        else ConfidenceLevel.medium
    )

    # Razon legible
    reason = _build_reason(deficit_ratio, ks, weighted_rain_3d, max_prob_3d, projected_ratio)

    return UrgencyResult(
        urgency_level=urgency,
        recommended_irrigation_mm=round(recommended_mm, 1),
        reason=reason,
        confidence=confidence
    )


def _build_reason(
    deficit_ratio: float,
    ks: float,
    weighted_rain_3d: float,
    max_prob_3d: float,
    projected_ratio: float,
) -> str:
    """Genera texto explicativo de la recomendación en lenguaje natural."""
    parts = []

    pct = round(deficit_ratio * 100)
    parts.append(f"Déficit hidrico actual: {pct}% de la capacidad disponible")

    if ks < 1.0:
        parts.append(f"Estres hidrico en curso (Ks={ks:.2f}).")

    if weighted_rain_3d > 5:
        parts.append(
            f"Lluvia esperada próximos 3 dias: {weighted_rain_3d:.1f}mm ponderados"
            f"(probabilidad máx. {max_prob_3d:.0f}%)."
        )
    else:
        parts.append("Sin lluvia significativa prevista en los próximos 3 días.")

    proj_pct = round(projected_ratio * 100)
    if proj_pct > pct + 10:
        parts.append(f"Proyección a 3 días: el déficit subirá al {proj_pct}%.")

    return " ".join(parts)