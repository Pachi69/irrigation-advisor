"""Pruebas del coeficiente de cultivo (Kc) de la vid.

Kc tabular: FAO-56 Tabla 12, pág. 112 (vid para vino: 0,30 / 0,70 / 0,45);
duración de las etapas según la Tabla 11, pág. 107, latitudes medias, vino
(30 / 60 / 40 / 80 días); interpolación lineal en desarrollo y etapa final
(Ec. 66, pág. 132). En reposo, Kc = 0,20.
Kc desde NDVI: Kc = Kc_ini + (Kc_mid − Kc_ini)·fc, con
fc = (NDVI − 0,15) / (0,85 − 0,15) acotado a [0, 1] (Glenn et al., 2011).
La temporada arranca en la brotación media de Mendoza, el 29/9
(Rodríguez et al., 2000).
"""
import unittest
from datetime import date, timedelta

from app.calculation.kc import calculate_kc
from app.models.enums import ConfidenceLevel, CropType, HailNetType, KcSource, PhenologicalStage
from app.schemas.satellite import SatelliteData

SEASON_START = date(2025, 9, 29)
MID_SEASON_DATE = date(2026, 1, 1)   # día 94 de la temporada: etapa media
DORMANCY_DATE = date(2026, 6, 1)


def _season_day(days: int) -> date:
    return SEASON_START + timedelta(days=days)

def _satellite(ndvi: float | None) -> SatelliteData:
    return SatelliteData(sector_id=1, date=MID_SEASON_DATE, ndvi=ndvi)


class TestKcTabular(unittest.TestCase):

    def test_stage_boundaries(self):
        cases = [
            (29, PhenologicalStage.initial),
            (30, PhenologicalStage.development),
            (89, PhenologicalStage.development),
            (90, PhenologicalStage.mid),
            (129, PhenologicalStage.mid),
            (130, PhenologicalStage.late),
            (209, PhenologicalStage.late),
            (210, PhenologicalStage.dormancy),
        ]
        for days, stage in cases:
            with self.subTest(days=days):
                result = calculate_kc(CropType.vine, _season_day(days), None)
                self.assertIs(result.phenological_stage, stage)

    def test_kc_by_stage(self):
        cases = [
            (0, 0.30),     # etapa inicial
            (60, 0.50),    # mitad del desarrollo: 0,30 + 0,5·(0,70 − 0,30)
            (100, 0.70),   # etapa media
            (170, 0.575),  # mitad de la etapa final: 0,70 + 0,5·(0,45 − 0,70)
            (210, 0.20),   # reposo
        ]
        for days, expected_kc in cases:
            with self.subTest(days=days):
                result = calculate_kc(CropType.vine, _season_day(days), None)
                self.assertAlmostEqual(result.kc, expected_kc, places=6)
                self.assertIs(result.source, KcSource.tabular)
                self.assertIs(result.kc_confidence, ConfidenceLevel.medium)

    def test_season_reanchoring(self):
        # El 28/9 todavía pertenece a la temporada anterior (reposo);
        # el 29/9 arranca la temporada nueva
        before = calculate_kc(CropType.vine, date(2026, 9, 28), None)
        start = calculate_kc(CropType.vine, date(2026, 9, 29), None)
        self.assertIs(before.phenological_stage, PhenologicalStage.dormancy)
        self.assertAlmostEqual(before.kc, 0.20, places=6)
        self.assertIs(start.phenological_stage, PhenologicalStage.initial)
        self.assertAlmostEqual(start.kc, 0.30, places=6)


class TestKcFromNdvi(unittest.TestCase):

    def test_kc_from_fractional_cover(self):
        cases = [
            (0.05, 0.30),  # bajo el NDVI de suelo desnudo: fc = 0
            (0.15, 0.30),
            (0.50, 0.50),  # fc = 0,5
            (0.85, 0.70),
            (0.95, 0.70),  # sobre el NDVI de cobertura completa: fc = 1 
        ]
        for ndvi, expected_kc in cases:
            with self.subTest(ndvi=ndvi):
                result = calculate_kc(CropType.vine, MID_SEASON_DATE, _satellite(ndvi))
                self.assertAlmostEqual(result.kc, expected_kc, places=6)
                self.assertIs(result.source, KcSource.s2_dynamic)
                self.assertIs(result.kc_confidence, ConfidenceLevel.high)

    def test_hail_net(self):
        # Malla abierta: el NDVI se usa con menor confianza.
        # Malla densa o de color: el NDVI no representa al cultivo, Kc tabular.
        cases = [
            (HailNetType.none, 0.50, KcSource.s2_dynamic, ConfidenceLevel.high),
            (HailNetType.open, 0.50, KcSource.s2_dynamic, ConfidenceLevel.medium),
            (HailNetType.dense, 0.70, KcSource.tabular, ConfidenceLevel.medium),
            (HailNetType.color, 0.70, KcSource.tabular, ConfidenceLevel.medium),
        ]
        for hail_net, expected_kc, source, confidence in cases:
            with self.subTest(hail_net=hail_net.value):
                result = calculate_kc(CropType.vine, MID_SEASON_DATE, _satellite(0.50), hail_net)
                self.assertAlmostEqual(result.kc, expected_kc, places=6)
                self.assertIs(result.source, source)
                self.assertIs(result.kc_confidence, confidence)

    def test_missing_ndvi(self):
        result = calculate_kc(CropType.vine, MID_SEASON_DATE, _satellite(None))
        self.assertAlmostEqual(result.kc, 0.70, places=6)
        self.assertIs(result.source, KcSource.tabular)

    def test_dormancy_ignores_ndvi(self):
        result = calculate_kc(CropType.vine, DORMANCY_DATE, _satellite(0.50))
        self.assertAlmostEqual(result.kc, 0.20, places=6)
        self.assertIs(result.source, KcSource.tabular)
        self.assertIs(result.phenological_stage, PhenologicalStage.dormancy)


if __name__ == "__main__":
    unittest.main()
