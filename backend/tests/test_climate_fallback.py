"""Pruebas del respaldo de NASA POWER cuando Open-Meteo no responde, sin red.

`httpx.get` es un único doble para las dos fuentes: según la URL, Open-Meteo
agota el tiempo y NASA POWER responde (o falla). Verifican que el respaldo
entrega el dato, que el valor de relleno -999 se trata como faltante, que el
balance calcula la ETo con FAO-56 cuando la fuente no la trae y que, en un
rango, un día sin datos se omite sin cortar el resto.
"""
import unittest
from datetime import date, timedelta
from unittest.mock import patch

import httpx

from app.calculation.eto import calculate_eto
from app.ingestion.climate import get_climate_data, get_climate_data_for_range
from app.ingestion.nasa_power import NASA_FILL_VALUE, NASA_POWER_URL
from app.ingestion import nasa_power
from app.services.water_balance import compute_balance_for_day
from tests._support import (
    ELEVATION_M, LATITUDE, LONGITUDE,
    make_field, make_sector, make_user, new_session, reset_database,
)

NASA_VALUES = {
    "T2M_MAX": 30.0,
    "T2M_MIN": 12.0,
    "T2M": 21.0,
    "RH2M": 50.0,
    "WS10M": 3.0,
    "ALLSKY_SFC_SW_DWN": 25.0,
    "PRECTOTCORR": 0.5,
    "PS": 93.1,
    "T2MDEW": 9.0,
}


def _nasa_response(day: date, **overrides: float) -> httpx.Response:
    day_key = day.strftime("%Y%m%d")
    values = {**NASA_VALUES, **overrides}
    payload = {"properties": {"parameter": {k: {day_key: v} for k, v in values.items()}}}
    return httpx.Response(200, json=payload, request=httpx.Request("GET", NASA_POWER_URL))


def _fake_get(failing_nasa_days: frozenset[date] = frozenset()):
    """Open-Meteo siempre agota el tiempo; NASA POWER responde salvo en `failing_nasa_days`."""
    def fake_get(url, params, timeout):
        if url != NASA_POWER_URL:
            raise httpx.TimeoutException("tiempo agotado")
        day = date(int(params["start"][:4]), int(params["start"][4:6]), int(params["start"][6:]))
        if day in failing_nasa_days:
            return httpx.Response(503, request=httpx.Request("GET", NASA_POWER_URL))
        return _nasa_response(day)
    return fake_get


class TestNasaPowerFallback(unittest.TestCase):

    def test_open_meteo_down_uses_nasa_power(self):
        yesterday = date.today() - timedelta(days=1)
        with patch("app.ingestion.climate.httpx.get", side_effect=_fake_get()) as get, \
             patch("app.ingestion.climate.time.sleep"), \
             self.assertLogs("app.ingestion.climate", "WARNING") as logs:
            climate = get_climate_data(LATITUDE, LONGITUDE, yesterday)

        urls = [c.args[0] for c in get.call_args_list]
        self.assertEqual(urls.count(NASA_POWER_URL), 1)
        self.assertEqual(len(urls), 4)  # 3 intentos a Open-Meteo y 1 a NASA POWER
        nasa_params = get.call_args.kwargs["params"]
        self.assertEqual(nasa_params["start"], yesterday.strftime("%Y%m%d"))
        self.assertEqual(nasa_params["end"], yesterday.strftime("%Y%m%d"))
        self.assertIn("NASA POWER como respaldo", logs.output[0])

        self.assertEqual(climate.date, yesterday)
        self.assertEqual(climate.temp_max_c, 30.0)
        self.assertEqual(climate.temp_min_c, 12.0)
        self.assertEqual(climate.temp_mean_c, 21.0)
        self.assertEqual(climate.humidity_pct, 50.0)
        self.assertEqual(climate.wind_speed_10m, 3.0)
        self.assertEqual(climate.solar_radiation_mj, 25.0)
        self.assertEqual(climate.precipitation_mm, 0.5)
        self.assertEqual(climate.pressure_kpa, 93.1)  # NASA POWER ya entrega kPa
        self.assertEqual(climate.dew_point_c, 9.0)
        self.assertIsNone(climate.eto_reference_mm)  # NASA POWER no trae ETo

    def test_fill_value_is_treated_as_missing(self):
        yesterday = date.today() - timedelta(days=1)
        optional = _nasa_response(yesterday, T2MDEW=NASA_FILL_VALUE)
        required = _nasa_response(yesterday, T2M_MAX=NASA_FILL_VALUE)
        with patch("app.ingestion.nasa_power.httpx.get", side_effect=[optional, required]):
            climate = nasa_power.get_climate_data(LATITUDE, LONGITUDE, yesterday)
            with self.assertRaisesRegex(RuntimeError, "temp_max_c"):
                nasa_power.get_climate_data(LATITUDE, LONGITUDE, yesterday)

        self.assertIsNone(climate.dew_point_c)
        self.assertEqual(climate.temp_max_c, 30.0)

    def test_both_sources_fail(self):
        yesterday = date.today() - timedelta(days=1)
        with patch("app.ingestion.climate.httpx.get", side_effect=_fake_get(frozenset({yesterday}))), \
             patch("app.ingestion.climate.time.sleep"), \
             self.assertLogs("app.ingestion.climate", "WARNING"):
            with self.assertRaisesRegex(RuntimeError, "Ambas fuentes fallaron.*Open-Meteo.*NASA POWER"):
                get_climate_data(LATITUDE, LONGITUDE, yesterday)

    def test_missing_pressure_is_a_source_failure(self):
        yesterday = date.today() - timedelta(days=1)
        response = _nasa_response(yesterday, PS=NASA_FILL_VALUE)
        with patch("app.ingestion.nasa_power.httpx.get", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "pressure_kpa"):
                nasa_power.get_climate_data(LATITUDE, LONGITUDE, yesterday)


class TestEToWithoutReference(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.db = new_session()
        self.sector = make_sector(self.db, make_field(self.db, make_user(self.db)))

    def tearDown(self):
        self.db.close()

    def test_balance_computes_eto_when_source_has_none(self):
        yesterday = date.today() - timedelta(days=1)
        with patch("app.ingestion.climate.httpx.get", side_effect=_fake_get()), \
             patch("app.ingestion.climate.time.sleep"), \
             self.assertLogs("app.ingestion.climate", "WARNING"):
            climate, eto, *_ = compute_balance_for_day(self.sector, yesterday, self.db)

        nasa_climate = climate.model_copy(update={"eto_reference_mm": None})
        expected = calculate_eto(nasa_climate, LATITUDE, yesterday, ELEVATION_M).eto_mm
        self.assertGreater(expected, 0.0)
        self.assertEqual(eto.eto_mm, expected)
        self.assertEqual(climate.eto_reference_mm, expected)


class TestRangeFallback(unittest.TestCase):

    def test_archive_down_fills_day_by_day_and_skips_failed_day(self):
        start = date.today() - timedelta(days=20)
        end = start + timedelta(days=3)  # todo el rango cae en el tramo de Archive
        failed_day = start + timedelta(days=1)
        with patch("app.ingestion.climate.httpx.get", side_effect=_fake_get(frozenset({failed_day}))), \
             patch("app.ingestion.climate.time.sleep"), \
             self.assertLogs("app.ingestion.climate", "WARNING") as logs:
            result = get_climate_data_for_range(LATITUDE, LONGITUDE, start, end)

        expected_days = [start + timedelta(days=i) for i in range(4) if i != 1]
        self.assertEqual(sorted(result), expected_days)
        self.assertTrue(all(c.temp_max_c == 30.0 for c in result.values()))
        self.assertTrue(any("Archive API fallo" in line for line in logs.output))
        self.assertTrue(any(f"NASA POWER fallo para {failed_day}" in line for line in logs.output))


if __name__ == "__main__":
    unittest.main()
