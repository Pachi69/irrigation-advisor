"""Pruebas del cliente de Open-Meteo con un doble de `httpx.get`, sin red.

Verifican la conversión de la respuesta al esquema del sistema (presión de
hPa a kPa, ETo de referencia, pronóstico) y la política de reintentos: hasta
3 intentos ante tiempo agotado, error HTTP o respuesta vacía, con esperas de
2 y 4 s entre intentos. `time.sleep` también es un doble, así que las
pruebas no esperan.
"""
import unittest
from datetime import date, timedelta
from unittest.mock import call, patch

import httpx

from app.ingestion.climate import OPEN_METEO_FORECAST_URL, get_climate_data, get_forecast


FULL_VALUES = {
    "temperature_2m_max": 31.0,
    "temperature_2m_min": 14.0,
    "temperature_2m_mean": 22.5,
    "relative_humidity_2m_mean": 45.0,
    "wind_speed_10m_mean": 2.5,
    "shortwave_radiation_sum": 27.0,
    "precipitation_sum": 1.2,
    "surface_pressure_mean": 934.0,
    "et0_fao_evapotranspiration": 6.2,
    "dew_point_2m_mean": 8.0,
}
FORECAST_VALUES = {
    "temperature_2m_max": 30.0,
    "temperature_2m_min": 15.0,
    "precipitation_sum": 4.0,
    "precipitation_probability_mean": 60.0,
    "et0_fao_evapotranspiration": 5.5,
}
EXPECTED_WAITS = [call(2.0), call(4.0)]


def _daily(dates: list[date], values: dict[str, float]) -> dict:
    return {"time": [d.isoformat() for d in dates], **{k: [v] * len(dates) for k, v in values.items()}}


def _response(payload: dict, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code, json=payload, request=httpx.Request("GET", OPEN_METEO_FORECAST_URL))


def _forecast_ok() -> httpx.Response:
    today = date.today()
    return _response({"daily": _daily([today + timedelta(days=i) for i in range(3)], FORECAST_VALUES)})


class TestOpenMeteoConversion(unittest.TestCase):

    def test_daily_row_to_climate_schema(self):
        yesterday = date.today() - timedelta(days=1)
        payload = {"daily": _daily([yesterday, date.today()], FULL_VALUES)}
        with patch("app.ingestion.climate.httpx.get", return_value=_response(payload)) as get:
            climate = get_climate_data(-10.0, -60.0, yesterday)

        params = get.call_args.kwargs["params"]
        self.assertEqual(params["past_days"], 1)
        self.assertEqual(params["wind_speed_unit"], "ms")
        self.assertEqual(climate.date, yesterday)
        self.assertEqual(climate.temp_max_c, 31.0)
        self.assertEqual(climate.temp_min_c, 14.0)
        self.assertEqual(climate.temp_mean_c, 22.5)
        self.assertEqual(climate.humidity_pct, 45.0)
        self.assertEqual(climate.wind_speed_10m, 2.5)
        self.assertEqual(climate.solar_radiation_mj, 27.0)
        self.assertEqual(climate.precipitation_mm, 1.2)
        self.assertAlmostEqual(climate.pressure_kpa, 93.4, places=9)
        self.assertEqual(climate.eto_reference_mm, 6.2)
        self.assertEqual(climate.dew_point_c, 8.0)

    def test_forecast_rows_to_schema(self):
        with patch("app.ingestion.climate.httpx.get", return_value=_forecast_ok()):
            forecast = get_forecast(-10.0, -60.0, days=3)

        self.assertEqual([d.date for d in forecast], [date.today() + timedelta(days=i) for i in range(3)])
        first = forecast[0]
        self.assertEqual(first.temp_max_c, 30.0)
        self.assertEqual(first.temp_min_c, 15.0)
        self.assertEqual(first.precipitation_mm, 4.0)
        self.assertEqual(first.precipitation_probability_pct, 60.0)
        self.assertEqual(first.eto_reference_mm, 5.5)


class TestOpenMeteoRetries(unittest.TestCase):

    def test_succeeds_on_second_attempt_after_timeout(self):
        effects = [httpx.TimeoutException("tiempo agotado"), _forecast_ok()]
        with patch("app.ingestion.climate.httpx.get", side_effect=effects) as get, \
             patch("app.ingestion.climate.time.sleep") as sleep:
            forecast = get_forecast(-10.0, -60.0, days=3)

        self.assertEqual(len(forecast), 3)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(sleep.call_args_list, [call(2.0)])

    def test_three_attempts_on_timeout(self):
        with patch("app.ingestion.climate.httpx.get", side_effect=httpx.TimeoutException("tiempo agotado")) as get, \
             patch("app.ingestion.climate.time.sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "tras 3 intentos"):
                get_forecast(-10.0, -60.0, days=3)

        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_args_list, EXPECTED_WAITS)

    def test_three_attempts_on_http_error(self):
        with patch("app.ingestion.climate.httpx.get", return_value=_response({}, status_code=500)) as get, \
             patch("app.ingestion.climate.time.sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "tras 3 intentos"):
                get_forecast(-10.0, -60.0, days=3)

        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_args_list, EXPECTED_WAITS)

    def test_three_attempts_on_empty_response(self):
        with patch("app.ingestion.climate.httpx.get", return_value=_response({"daily": {}})) as get, \
             patch("app.ingestion.climate.time.sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "tras 3 intentos"):
                get_forecast(-10.0, -60.0, days=3)

        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_args_list, EXPECTED_WAITS)


class TestOpenMeteoDateLimits(unittest.TestCase):

    def test_invalid_dates_fail_before_requesting(self):
        today = date.today()
        with patch("app.ingestion.climate.httpx.get") as get:
            with self.assertRaises(ValueError):
                get_climate_data(-10.0, -60.0, today + timedelta(days=1))
            with self.assertRaises(ValueError):
                get_climate_data(-10.0, -60.0, today - timedelta(days=93))
            with self.assertRaises(ValueError):
                get_forecast(-10.0, -60.0, days=0)
            with self.assertRaises(ValueError):
                get_forecast(-10.0, -60.0, days=17)

        get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
