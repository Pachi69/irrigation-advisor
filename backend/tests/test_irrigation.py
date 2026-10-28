"""Pruebas de la conversión entre lámina neta (mm) y volumen o tiempo de riego.

1 mm sobre 1 ha = 10 m³ = 10.000 L. El volumen y el tiempo son brutos: la
lámina neta dividida por la eficiencia de aplicación del método de riego
(superficial 0,60; aspersión 0,85; DGI y Schilardi et al., 2015).
"""
import unittest

from app.calculation.irrigation import (
    efficiency_for,
    mm_to_time_min,
    mm_to_volume_m3,
    time_min_to_mm,
    volume_m3_to_mm,
)
from app.models.enums import IrrigationType

ASPERSION_EFFICIENCY = 0.85
SUPERFICIAL_EFFICIENCY = 0.60


class TestIrrigationConversions(unittest.TestCase):

    def test_efficiency_by_method(self):
        self.assertAlmostEqual(efficiency_for(IrrigationType.superficial), SUPERFICIAL_EFFICIENCY, places=9)
        self.assertAlmostEqual(efficiency_for(IrrigationType.aspersion), ASPERSION_EFFICIENCY, places=9)

    def test_mm_to_volume(self):
        cases = [
            (10.0, 1.0, ASPERSION_EFFICIENCY, 117.65),     # 10·1·10/0,85
            (10.0, 2.5, SUPERFICIAL_EFFICIENCY, 416.67),   # 10·2,5·10/0,60
        ]
        for lamina_mm, area_ha, eff, expected_m3 in cases:
            with self.subTest(area_ha=area_ha, eff=eff):
                volume_m3 = mm_to_volume_m3(lamina_mm, area_ha, eff)
                assert volume_m3 is not None
                self.assertAlmostEqual(volume_m3, expected_m3, delta=0.01)

    def test_mm_to_time(self):
        # 10 mm con 10 L/s/ha: 10·10.000 / (10·0,85) / 60
        time_min = mm_to_time_min(10.0, 10.0, ASPERSION_EFFICIENCY)
        assert time_min is not None
        self.assertAlmostEqual(time_min, 196.08, delta=0.01)

    def test_volume_round_trip(self):
        volume_m3 = mm_to_volume_m3(10.0, 2.5, ASPERSION_EFFICIENCY)
        assert volume_m3 is not None
        self.assertAlmostEqual(volume_m3_to_mm(volume_m3, 2.5, ASPERSION_EFFICIENCY), 10.0, places=9)

    def test_time_round_trip(self):
        time_min = mm_to_time_min(10.0, 10.0, ASPERSION_EFFICIENCY)
        assert time_min is not None
        self.assertAlmostEqual(time_min_to_mm(time_min, 10.0, ASPERSION_EFFICIENCY), 10.0, places=9)

    def test_missing_area_or_flow(self):
        # Sin área o caudal cargados no hay volumen ni tiempo para mostrar
        self.assertIsNone(mm_to_volume_m3(10.0, None, ASPERSION_EFFICIENCY))
        self.assertIsNone(mm_to_volume_m3(10.0, 0.0, ASPERSION_EFFICIENCY))
        self.assertIsNone(mm_to_volume_m3(10.0, 1.0, 0.0))
        self.assertIsNone(mm_to_time_min(10.0, None, ASPERSION_EFFICIENCY))
        self.assertIsNone(mm_to_time_min(10.0, 10.0, 0.0))
        # En la carga de un riego, sin tiempo, caudal o área la lámina es 0
        self.assertEqual(time_min_to_mm(None, 10.0, ASPERSION_EFFICIENCY), 0.0)
        self.assertEqual(time_min_to_mm(30.0, None, ASPERSION_EFFICIENCY), 0.0)
        self.assertEqual(volume_m3_to_mm(100.0, None, ASPERSION_EFFICIENCY), 0.0)


if __name__ == "__main__":
    unittest.main()
