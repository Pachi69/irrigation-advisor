"""Pruebas del índice de urgencia de riego.

FAO-56 fija el momento de riego en Dr = RAW (Ec. 83, pág. 163) pero no
define niveles de urgencia: los niveles, las sub-bandas de Ks (0,75 y 0,5),
la proyección a 3 días, la baja por lluvia pronosticada y el colchón para
lluvia son reglas del sistema (app/calculation/urgency.py). Los valores
esperados salen de aplicar esas reglas a mano.

Salvo que se indique otra cosa: TAW = 100 mm, RAW = 50 mm, Kc = 1.
Ks = 0,75 con Dr = 62,5 mm; Ks = 0,5 con Dr = 75 mm.
"""
import unittest
from datetime import date, timedelta

from app.calculation.urgency import calculate_urgency, urgency_from_balance
from app.models.enums import ConfidenceLevel, KcSource, PhenologicalStage, UrgencyLevel
from app.schemas.calculation import KcResult, WaterBalanceResult
from app.schemas.climate import ForecastDay

FIRST_FORECAST_DATE = date(2026, 1, 2)
KC = KcResult(
    kc=1.0,
    source=KcSource.tabular,
    phenological_stage=PhenologicalStage.mid,
    kc_confidence=ConfidenceLevel.medium,
)


def _balance(deficit_mm: float, ks: float, taw_mm: float = 100.0, raw_mm: float = 50.0) -> WaterBalanceResult:
    return WaterBalanceResult(
        water_deficit_mm=deficit_mm,
        ks=ks,
        taw_mm=taw_mm,
        raw_mm=raw_mm,
        deep_percolation_mm=0.0,
    )


def _forecast(days: list[tuple[float, float, float]]) -> list[ForecastDay]:
    """Pronóstico desde tuplas (ETo mm, lluvia mm, probabilidad de lluvia %)."""
    return [
        ForecastDay(
            date=FIRST_FORECAST_DATE + timedelta(days=i),
            temp_max_c=30.0,
            temp_min_c=15.0,
            precipitation_mm=precipitation_mm,
            precipitation_probability_pct=probability_pct,
            eto_reference_mm=eto_mm,
        )
        for i, (eto_mm, precipitation_mm, probability_pct) in enumerate(days)
    ]


# Sin demanda ni lluvia: el déficit proyectado no cambia y no hay colchón
NEUTRAL_FORECAST = _forecast([(0.0, 0.0, 0.0)] * 3)


class TestUrgencyBands(unittest.TestCase):

    def test_bands(self):
        cases = [
            (49.0, 1.00, UrgencyLevel.low, 0.0),         # Dr < RAW
            (51.0, 0.98, UrgencyLevel.medium, 51.0),     # Dr > RAW
            (62.0, 0.76, UrgencyLevel.medium, 62.0),     # Ks ≥ 0,75
            (63.0, 0.74, UrgencyLevel.high, 63.0),       # Ks < 0,75
            (74.0, 0.52, UrgencyLevel.high, 74.0),       # Ks ≥ 0,5
            (76.0, 0.48, UrgencyLevel.critical, 76.0),   # Ks < 0,5
        ]
        for deficit_mm, ks, level, irrigation_mm in cases:
            with self.subTest(deficit_mm=deficit_mm):
                result = calculate_urgency(_balance(deficit_mm, ks), NEUTRAL_FORECAST, KC)
                self.assertIs(result.urgency_level, level)
                self.assertAlmostEqual(result.recommended_irrigation_mm, irrigation_mm, places=6)

    def test_deficit_equal_to_raw(self):
        # En Dr = RAW todavía es Ks = 1, pero ya se recomienda regar
        result = calculate_urgency(_balance(50.0, 1.0), NEUTRAL_FORECAST, KC)
        self.assertIs(result.urgency_level, UrgencyLevel.medium)
        self.assertAlmostEqual(result.recommended_irrigation_mm, 50.0, places=6)

    def test_confidence_from_kc(self):
        kc = KC.model_copy(update={"kc_confidence": ConfidenceLevel.high})
        result = calculate_urgency(_balance(55.0, 0.9), NEUTRAL_FORECAST, kc)
        self.assertIs(result.confidence, ConfidenceLevel.high)


class TestUrgencyForecastRules(unittest.TestCase):

    def test_upgrade_by_projection(self):
        # Dr proyectado = 45 + 3·3 = 54 ≥ RAW → sube de baja a media
        result = calculate_urgency(_balance(45.0, 1.0), _forecast([(3.0, 0.0, 0.0)] * 3), KC)
        self.assertIs(result.urgency_level, UrgencyLevel.medium)
        self.assertAlmostEqual(result.recommended_irrigation_mm, 45.0, places=6)

    def test_downgrade_from_medium(self):
        # Lluvia ponderada 60·1,0 = 60 > Dr = 55, probabilidad ≥ 70 → pasa a baja
        forecast = _forecast([(5.0, 60.0, 100.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)])
        result = calculate_urgency(_balance(55.0, 0.9), forecast, KC)
        self.assertIs(result.urgency_level, UrgencyLevel.low)
        self.assertAlmostEqual(result.recommended_irrigation_mm, 0.0, places=6)

    def test_downgrade_from_high(self):
        # Lluvia ponderada 50·0,8 = 40 > 0,5·65, probabilidad ≥ 70 → baja a media;
        # colchón = min(40, RAW/2) = 25 → 65 − 25 = 40
        forecast = _forecast([(1.0, 50.0, 80.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)])
        result = calculate_urgency(_balance(65.0, 0.7), forecast, KC)
        self.assertIs(result.urgency_level, UrgencyLevel.medium)
        self.assertAlmostEqual(result.recommended_irrigation_mm, 40.0, places=6)

    def test_downgrade_from_critical(self):
        # TAW = 20, RAW = 10, Dr = 14,8 (Ks = 0,52: alta).
        # Proyección: 14,8 − 10·0,9 + 3·4 = 17,8 (Ks = 0,22) → sube a crítica.
        # Lluvia ponderada 9 > 0,6·14,8 = 8,88, probabilidad ≥ 80 → baja a alta.
        # Colchón = min(9, RAW/2) = 5 → 14,8 − 5 = 9,8
        forecast = _forecast([(4.0, 10.0, 90.0), (4.0, 0.0, 0.0), (4.0, 0.0, 0.0)])
        result = calculate_urgency(_balance(14.8, 0.52, taw_mm=20.0, raw_mm=10.0), forecast, KC)
        self.assertIs(result.urgency_level, UrgencyLevel.high)
        self.assertAlmostEqual(result.recommended_irrigation_mm, 9.8, places=6)

    def test_no_downgrade_below_critical_ks(self):
        # Con Ks < 0,5 no baja aunque llueva seguro, y repone todo el déficit
        forecast = _forecast([(5.0, 100.0, 100.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)])
        result = calculate_urgency(_balance(76.0, 0.48), forecast, KC)
        self.assertIs(result.urgency_level, UrgencyLevel.critical)
        self.assertAlmostEqual(result.recommended_irrigation_mm, 76.0, places=6)

    def test_rain_buffer(self):
        # Lluvia ponderada 10·0,5 = 5 → colchón 5 → 60 − 5 = 55
        forecast = _forecast([(5.0, 10.0, 50.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)])
        result = calculate_urgency(_balance(60.0, 0.8), forecast, KC)
        self.assertIs(result.urgency_level, UrgencyLevel.medium)
        self.assertAlmostEqual(result.recommended_irrigation_mm, 55.0, places=6)

    def test_rain_buffer_capped(self):
        # Lluvia ponderada 80·0,5 = 40 → colchón acotado a RAW/2 = 25 → 60 − 25 = 35
        forecast = _forecast([(5.0, 80.0, 50.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)])
        result = calculate_urgency(_balance(60.0, 0.8), forecast, KC)
        self.assertIs(result.urgency_level, UrgencyLevel.medium)
        self.assertAlmostEqual(result.recommended_irrigation_mm, 35.0, places=6)


class TestUrgencyFromBalance(unittest.TestCase):

    def test_without_forecast(self):
        # Sin pronóstico: urgencia por déficit y repone todo el déficit
        cases = [
            (49.0, 1.00, UrgencyLevel.low, 0.0),
            (55.0, 0.90, UrgencyLevel.medium, 55.0),
            (76.0, 0.48, UrgencyLevel.critical, 76.0),
        ]
        for deficit_mm, ks, level, irrigation_mm in cases:
            with self.subTest(deficit_mm=deficit_mm):
                result = urgency_from_balance(_balance(deficit_mm, ks), KC)
                self.assertIs(result.urgency_level, level)
                self.assertAlmostEqual(result.recommended_irrigation_mm, irrigation_mm, places=6)


if __name__ == "__main__":
    unittest.main()
