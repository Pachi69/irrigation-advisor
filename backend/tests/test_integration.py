"""Prueba de integración del motor de cálculo: clima → ETo → Kc → balance →
urgencia → volumen y tiempo de riego.

Clima del Ejemplo 18 de FAO-56 (ETo = 3,88 mm, págs. 72-73); vid en etapa
media con NDVI 0,50 (Kc = 0,50); suelo franco con Zr = 1 m y p = 0,5
(TAW = 140 mm, RAW = 70 mm); déficit inicial de 70 mm; riego por aspersión
sobre 1 ha con 10 L/s/ha. Los valores esperados salen de encadenar a mano
las fórmulas que verifican las demás pruebas.
"""
import unittest
from datetime import date, timedelta

from app.calculation.eto import _saturation_vapor_pressure, calculate_eto
from app.calculation.irrigation import efficiency_for, mm_to_time_min, mm_to_volume_m3
from app.calculation.kc import calculate_kc
from app.calculation.urgency import calculate_urgency
from app.calculation.water_balance import calculate_water_balance
from app.models.enums import ConfidenceLevel, CropType, IrrigationType, KcSource, SoilType, UrgencyLevel
from app.schemas.climate import ClimateData, ForecastDay
from app.schemas.satellite import SatelliteData

# Clima del Ejemplo 18 (ver test_eto.py)
LATITUDE_DEG = 50.80
ELEVATION_M = 100.0
TEMP_MAX_C = 21.5
TEMP_MIN_C = 12.3
ACTUAL_VAPOR_PRESSURE_KPA = 1.409
ETO_DATE = date(2026, 7, 6)

CROP_DATE = date(2026, 1, 1)        # etapa media de la vid
NDVI = 0.50
SOIL = SoilType.loam
ROOT_DEPTH_M = 1.0
DEPLETION_FACTOR = 0.5
START_DEFICIT_MM = 70.0
AREA_HA = 1.0
FLOW_LS_HA = 10.0


def _climate() -> ClimateData:
    es = (_saturation_vapor_pressure(TEMP_MAX_C) + _saturation_vapor_pressure(TEMP_MIN_C)) / 2
    return ClimateData(
        date=ETO_DATE,
        temp_max_c=TEMP_MAX_C,
        temp_min_c=TEMP_MIN_C,
        temp_mean_c=16.9,
        humidity_pct=ACTUAL_VAPOR_PRESSURE_KPA / es * 100,
        wind_speed_10m=10 / 3.6,
        solar_radiation_mj=22.07,
        precipitation_mm=0.0,
        pressure_kpa=100.1,
    )


def _neutral_forecast() -> list[ForecastDay]:
    # Sin demanda ni lluvia: la urgencia depende solo del balance
    return [
        ForecastDay(
            date=CROP_DATE + timedelta(days=i + 1),
            temp_max_c=30.0,
            temp_min_c=15.0,
            precipitation_mm=0.0,
            precipitation_probability_pct=0.0,
            eto_reference_mm=0.0,
        )
        for i in range(3)
    ]


class TestCalculationChain(unittest.TestCase):

    def test_full_chain(self):
        eto = calculate_eto(_climate(), LATITUDE_DEG, ETO_DATE, elevation_m=ELEVATION_M)
        self.assertAlmostEqual(eto.eto_mm, 3.88, delta=0.005)

        satellite = SatelliteData(sector_id=1, date=CROP_DATE, ndvi=NDVI)
        kc = calculate_kc(CropType.vine, CROP_DATE, satellite)
        self.assertAlmostEqual(kc.kc, 0.50, places=6)
        self.assertIs(kc.source, KcSource.s2_dynamic)

        # Dr inicial = RAW, Ks = 1: Dr = 70 + 0,50·3,88 = 71,94
        # Ks al final del día = (140 − 71,94)/(140 − 70) = 0,9723
        balance = calculate_water_balance(
            eto, kc,
            precipitation_mm=0.0, previous_deficit_mm=START_DEFICIT_MM,
            soil_type=SOIL, root_depth_m=ROOT_DEPTH_M, depletion_factor_p=DEPLETION_FACTOR,
        )
        self.assertAlmostEqual(balance.taw_mm, 140.0, places=6)
        self.assertAlmostEqual(balance.raw_mm, 70.0, places=6)
        self.assertAlmostEqual(balance.water_deficit_mm, 71.94, delta=0.005)
        self.assertAlmostEqual(balance.ks, 0.9723, delta=0.0001)

        # Dr > RAW con Ks ≥ 0,75: urgencia media; se repone el déficit,
        # redondeado a 0,1 mm. La confianza es la del Kc satelital.
        urgency = calculate_urgency(balance, _neutral_forecast(), kc)
        self.assertIs(urgency.urgency_level, UrgencyLevel.medium)
        self.assertAlmostEqual(urgency.recommended_irrigation_mm, 71.9, places=6)
        self.assertIs(urgency.confidence, ConfidenceLevel.high)

        # 71,9·1·10/0,85 = 845,88 m³; 71,9·10.000/(10·0,85)/60 = 1409,80 min
        efficiency = efficiency_for(IrrigationType.aspersion)
        volume_m3 = mm_to_volume_m3(urgency.recommended_irrigation_mm, AREA_HA, efficiency)
        time_min = mm_to_time_min(urgency.recommended_irrigation_mm, FLOW_LS_HA, efficiency)
        assert volume_m3 is not None
        assert time_min is not None
        self.assertAlmostEqual(volume_m3, 845.88, delta=0.01)
        self.assertAlmostEqual(time_min, 1409.80, delta=0.01)


if __name__ == "__main__":
    unittest.main()
