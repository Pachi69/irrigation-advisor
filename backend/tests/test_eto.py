"""Pruebas de la ETo FAO-56 Penman-Monteith contra el Ejemplo 18 de FAO-56.

El sistema usa la ETo de Open-Meteo (et0_fao_evapotranspiration); calculate_eto
es el respaldo cuando ese dato falta. Estas pruebas verifican ese respaldo.

Fuente: Allen et al. (1998), FAO-56, Ejemplo 18, págs. 72-73.
Tolerancia: la mitad del último dígito publicado en el ejemplo.
"""
import math
import unittest
from datetime import date

from app.calculation.eto import (
    _elevation_from_pressure,
    _extraterrestrial_radiation,
    _psychrometric_constant,
    _saturation_vapor_pressure,
    _slope_vapor_pressure_curve,
    _wind_speed_2m,
    calculate_eto,
)
from app.schemas.climate import ClimateData

# Datos del Ejemplo 18: Uccle (Bélgica), 6 de julio
LATITUDE_DEG = 50.80                # 50°48'N
ELEVATION_M = 100.0
PRESSURE_KPA = 100.1
TEMP_MAX_C = 21.5
TEMP_MIN_C = 12.3
TEMP_MEAN_C = 16.9
WIND_SPEED_10M_MS = 10 / 3.6        # 10 km/h medido a 10 m
SOLAR_RADIATION_MJ = 22.07          # Rs calculada en el ejemplo desde n = 9,25 h
ACTUAL_VAPOR_PRESSURE_KPA = 1.409   # ea calculada en el ejemplo desde RHmax y RHmin
DEW_POINT_C = 12.07                 # punto de rocío equivalente: e°(12,07) = 1,409 kPa
DAY_OF_YEAR = 187
TARGET_DATE = date(2026, 7, 6)      # día 187 en un año no bisiesto


class TestEtoFao56Example18(unittest.TestCase):

    def test_psychrometric_constant(self):
        self.assertAlmostEqual(_psychrometric_constant(PRESSURE_KPA), 0.0666, delta=0.00005)

    def test_slope_vapor_pressure_curve(self):
        self.assertAlmostEqual(_slope_vapor_pressure_curve(TEMP_MEAN_C), 0.122, delta=0.0005)

    def test_saturation_vapor_pressure(self):
        for temp_c, expected_kpa in [(TEMP_MAX_C, 2.564), (TEMP_MIN_C, 1.431)]:
            with self.subTest(temp_c=temp_c):
                self.assertAlmostEqual(_saturation_vapor_pressure(temp_c), expected_kpa, delta=0.0005)

    def test_wind_speed_2m(self):
        self.assertAlmostEqual(_wind_speed_2m(WIND_SPEED_10M_MS), 2.078, delta=0.0005)

    def test_extraterrestrial_radiation(self):
        ra = _extraterrestrial_radiation(math.radians(LATITUDE_DEG), DAY_OF_YEAR)
        self.assertAlmostEqual(ra, 41.09, delta=0.005)

    def test_elevation_from_pressure(self):
        # El ejemplo obtiene P = 100,1 kPa desde z = 100m y la redondea;
        # invertir la P redondeada da unos 102m
        self.assertAlmostEqual(_elevation_from_pressure(PRESSURE_KPA), ELEVATION_M, delta=3.0)

    def test_eto(self):
        es = (_saturation_vapor_pressure(TEMP_MAX_C) +
              _saturation_vapor_pressure(TEMP_MIN_C)) / 2
        climate = ClimateData(
            date=TARGET_DATE,
            temp_max_c=TEMP_MAX_C,
            temp_min_c=TEMP_MIN_C,
            temp_mean_c=TEMP_MEAN_C,
            # HR media equivalente a la ea del ejemplo: ea = HR/100 * es
            humidity_pct=ACTUAL_VAPOR_PRESSURE_KPA / es * 100,
            wind_speed_10m=WIND_SPEED_10M_MS,
            solar_radiation_mj=SOLAR_RADIATION_MJ,
            precipitation_mm=0.0,
            pressure_kpa=PRESSURE_KPA,
            dew_point_c=None,
        )
        result = calculate_eto(climate, LATITUDE_DEG, TARGET_DATE, elevation_m=ELEVATION_M)
        self.assertAlmostEqual(result.eto_mm, 3.88, delta=0.005)

    def test_eto_from_dew_point(self):
        # Con punto de rocío, ea sale de la Ec. 14 y la HR no se usa:
        # con una HR distinta a la del ejemplo la ETo tiene que dar igual
        climate = ClimateData(
            date=TARGET_DATE,
            temp_max_c=TEMP_MAX_C,
            temp_min_c=TEMP_MIN_C,
            temp_mean_c=TEMP_MEAN_C,
            humidity_pct=50.0,
            wind_speed_10m=WIND_SPEED_10M_MS,
            solar_radiation_mj=SOLAR_RADIATION_MJ,
            precipitation_mm=0.0,
            pressure_kpa=PRESSURE_KPA,
            dew_point_c=DEW_POINT_C,
        )
        result = calculate_eto(climate, LATITUDE_DEG, TARGET_DATE, elevation_m=ELEVATION_M)
        self.assertAlmostEqual(result.eto_mm, 3.88, delta=0.005)


if __name__ == "__main__":
    unittest.main() 
