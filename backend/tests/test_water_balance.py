"""Pruebas del balance hídrico diario en la zona radicular (FAO-56, cap. 8).

TAW = 1000·(θFC − θWP)·Zr (Ec. 82, pág. 162); RAW = p·TAW (Ec. 83, pág. 163);
Ks = (TAW − Dr)/(TAW − RAW) si Dr > RAW (Ec. 84, pág. 169);
Dr,i = Dr,i-1 − (P − RO)i − Ii + ETc,i + DPi (Ec. 85, pág. 170), con RO = 0;
el excedente sobre capacidad de campo percola (Ec. 88, pág. 171);
la lluvia menor a 0,2·ETo se ignora (pág. 170).
El Ejemplo 37 (pág. 168) se reproduce día a día. Tolerancia: la mitad del
último dígito publicado en el ejemplo.
"""
import unittest

from app.calculation.water_balance import calculate_water_balance, effective_precipitation
from app.models.enums import ConfidenceLevel, KcSource, PhenologicalStage, SoilType
from app.schemas.calculation import EToResult, KcResult

# Ejemplo 37: suelo limoso con θFC − θWP = 0,20, igual que silt_loam (0,31 − 0,11)
EXAMPLE_37_SOIL = SoilType.silt_loam
EXAMPLE_37_ROOT_DEPTH_M = 0.8
EXAMPLE_37_DEPLETION_FACTOR = 0.40
EXAMPLE_37_ETO_MM = 5.0
EXAMPLE_37_KC = 1.2
# Por día: (Dr al inicio del día, Ks, ETc ajustada), días 1 a 10
EXAMPLE_37_DAYS = [
    (55.0, 1.00, 6.0),
    (61.0, 1.00, 6.0),
    (67.0, 0.97, 5.8),
    (72.8, 0.91, 5.4),
    (78.3, 0.85, 5.1),
    (83.4, 0.80, 4.8),
    (88.2, 0.75, 4.5),
    (92.6, 0.70, 4.2),
    (96.9, 0.66, 3.9),
    (100.8, 0.62, 3.7),
]
EXAMPLE_37_FINAL_DEFICIT_MM = 104.5


def _kc(value: float) -> KcResult:
    return KcResult(
        kc=value,
        source=KcSource.tabular,
        phenological_stage=PhenologicalStage.mid,
        kc_confidence=ConfidenceLevel.medium,
    )


class TestWaterBalanceFao56Example37(unittest.TestCase):

    def test_example_37(self):
        deficit_mm = EXAMPLE_37_DAYS[0][0]
        # El Ks del ejemplo usa el agotamiento al inicio del día, que es el Ks
        # que el motor devuelve al final del día anterior; el día 1 tiene Ks = 1
        start_ks = 1.0
        for day, (start_deficit_mm, expected_ks, expected_etc_adj_mm) in enumerate(EXAMPLE_37_DAYS, start=1):
            with self.subTest(day=day):
                result = calculate_water_balance(
                    EToResult(eto_mm=EXAMPLE_37_ETO_MM),
                    _kc(EXAMPLE_37_KC),
                    precipitation_mm=0.0,
                    previous_deficit_mm=deficit_mm,
                    soil_type=EXAMPLE_37_SOIL,
                    root_depth_m=EXAMPLE_37_ROOT_DEPTH_M,
                    depletion_factor_p=EXAMPLE_37_DEPLETION_FACTOR,
                )
                self.assertAlmostEqual(result.taw_mm, 160.0, places=6)
                self.assertAlmostEqual(result.raw_mm, 64.0, places=6)
                self.assertAlmostEqual(deficit_mm, start_deficit_mm, delta=0.05)
                # Sin lluvia ni riego, la ETc ajustada es lo que crece el déficit
                self.assertAlmostEqual(result.water_deficit_mm - deficit_mm, expected_etc_adj_mm, delta=0.05)
                self.assertAlmostEqual(start_ks, expected_ks, delta=0.005)
                start_ks = result.ks
                deficit_mm = result.water_deficit_mm
        self.assertAlmostEqual(deficit_mm, EXAMPLE_37_FINAL_DEFICIT_MM, delta=0.05)


class TestWaterBalanceRules(unittest.TestCase):

    def test_rain_and_irrigation(self):
        # loam: TAW = 1000·(0,28 − 0,14)·1,0 = 140; Dr = 40 − 10 − 15 + 0,8·5 = 19
        result = calculate_water_balance(
            EToResult(eto_mm=5.0), _kc(0.8),
            precipitation_mm=10.0, previous_deficit_mm=40.0,
            soil_type=SoilType.loam, root_depth_m=1.0, depletion_factor_p=0.5,
            irrigation_mm=15.0,
        )
        self.assertAlmostEqual(result.taw_mm, 140.0, places=6)
        self.assertAlmostEqual(result.raw_mm, 70.0, places=6)
        self.assertAlmostEqual(result.water_deficit_mm, 19.0, places=9)
        self.assertAlmostEqual(result.ks, 1.0, places=9)
        self.assertAlmostEqual(result.deep_percolation_mm, 0.0, places=9)

    def test_deep_percolation(self):
        # 10 − 30 + 5 = −15: el suelo queda a capacidad de campo y percolan 15 mm
        result = calculate_water_balance(
            EToResult(eto_mm=5.0), _kc(1.0),
            precipitation_mm=30.0, previous_deficit_mm=10.0,
            soil_type=SoilType.loam, root_depth_m=1.0, depletion_factor_p=0.5,
        )
        self.assertAlmostEqual(result.water_deficit_mm, 0.0, places=9)
        self.assertAlmostEqual(result.deep_percolation_mm, 15.0, places=9)

    def test_deficit_capped_at_taw(self):
        # sand: TAW = 1000·(0,10 − 0,05)·0,4 = 20, RAW = 18;
        # Ks = (20 − 19)/(20 − 18) = 0,5 → 19 + 0,5·6 = 22, acotado a TAW
        result = calculate_water_balance(
            EToResult(eto_mm=6.0), _kc(1.0),
            precipitation_mm=0.0, previous_deficit_mm=19.0,
            soil_type=SoilType.sand, root_depth_m=0.4, depletion_factor_p=0.9,
        )
        self.assertAlmostEqual(result.water_deficit_mm, 20.0, places=9)
        self.assertAlmostEqual(result.ks, 0.0, places=9)

    def test_light_rain_ignored(self):
        # 0,9 mm < 0,2·5 mm: no entra al balance; Dr = 30 + 5 = 35
        result = calculate_water_balance(
            EToResult(eto_mm=5.0), _kc(1.0),
            precipitation_mm=0.9, previous_deficit_mm=30.0,
            soil_type=SoilType.loam, root_depth_m=1.0, depletion_factor_p=0.5,
        )
        self.assertAlmostEqual(result.water_deficit_mm, 35.0, places=9)


class TestEffectivePrecipitation(unittest.TestCase):

    def test_threshold(self):
        cases = [
            (0.0, 0.0),
            (0.9, 0.0),    # menor a 0,2·ETo
            (1.0, 1.0),    # igual a 0,2·ETo: cuenta entera
            (10.0, 10.0),
        ]
        for precipitation_mm, expected_mm in cases:
            with self.subTest(precipitation_mm=precipitation_mm):
                self.assertAlmostEqual(effective_precipitation(precipitation_mm, 5.0), expected_mm, places=9)


if __name__ == "__main__":
    unittest.main()
