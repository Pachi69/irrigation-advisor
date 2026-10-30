"""Pruebas de la validación de los datos climáticos externos, sin red.

La validación debe rechazar con `RuntimeError` todo campo que el esquema
exige, porque ese es el error que atrapan el respaldo de NASA POWER y el
relleno por rango. Un valor fuera de rango físico solo se advierte en el log.
"""
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from app.ingestion.climate import get_climate_data, get_forecast
from app.ingestion.nasa_power import NASA_POWER_URL
from app.ingestion.validation import (
    REQUIRED_FIELDS_CLIMATE, REQUIRED_FIELDS_FORECAST,
    validate_climate_row, validate_forecast_row,
)
from app.schemas.climate import ClimateData, ForecastDay
from tests.test_climate_fallback import _nasa_response
from tests.test_open_meteo import FORECAST_VALUES, FULL_VALUES, _daily, _response


CLIMATE_ROW = {
    "temp_max_c": 31.0, "temp_min_c": 14.0, "temp_mean_c": 22.5,
    "humidity_pct": 45.0, "wind_speed_10m": 2.5, "solar_radiation_mj": 27.0,
    "precipitation_mm": 0.0, "pressure_kpa": 93.4,
    "eto_reference_mm": 6.2, "dew_point_c": 8.0,
}
FORECAST_ROW = {
    "temp_max_c": 30.0, "temp_min_c": 15.0, "precipitation_mm": 4.0,
    "precipitation_probability_pct": 60.0, "eto_reference_mm": 5.5,
}


def _schema_required(schema: type[ClimateData] | type[ForecastDay]) -> set[str]:
    return {name for name, info in schema.model_fields.items() if info.is_required()} - {"date"}


class TestRequiredFields(unittest.TestCase):

    def test_climate_rejects_every_field_the_schema_requires(self):
        self.assertLessEqual(_schema_required(ClimateData), REQUIRED_FIELDS_CLIMATE)
        for field in sorted(REQUIRED_FIELDS_CLIMATE):
            with self.subTest(field=field):
                with self.assertRaisesRegex(RuntimeError, field):
                    validate_climate_row({**CLIMATE_ROW, field: None})

        optional = {**CLIMATE_ROW, "eto_reference_mm": None, "dew_point_c": None}
        self.assertIs(validate_climate_row(optional), optional)

    def test_forecast_rejects_every_field_the_schema_requires(self):
        self.assertLessEqual(_schema_required(ForecastDay), REQUIRED_FIELDS_FORECAST)
        for field in sorted(REQUIRED_FIELDS_FORECAST):
            with self.subTest(field=field):
                with self.assertRaisesRegex(RuntimeError, field):
                    validate_forecast_row({**FORECAST_ROW, field: None})

        today = date.today()
        daily = _daily([today + timedelta(days=i) for i in range(3)], FORECAST_VALUES)
        daily["precipitation_probability_mean"][2] = None
        with patch("app.ingestion.climate.httpx.get", return_value=_response({"daily": daily})):
            with self.assertRaisesRegex(RuntimeError, "precipitation_probability_pct"):
                get_forecast(-10.0, -60.0, days=3)


class TestPhysicalRanges(unittest.TestCase):

    def test_out_of_range_value_is_logged_and_kept(self):
        row = {**CLIMATE_ROW, "humidity_pct": 120.0}
        with self.assertLogs("app.ingestion.validation", "WARNING") as logs:
            result = validate_climate_row(row)

        self.assertEqual(result["humidity_pct"], 120.0)
        self.assertEqual(len(logs.output), 1)
        self.assertIn("humidity_pct", logs.output[0])
        with self.assertNoLogs("app.ingestion.validation", "WARNING"):
            validate_climate_row(CLIMATE_ROW)
            validate_forecast_row(FORECAST_ROW)


class TestInvalidRowFallback(unittest.TestCase):

    def test_open_meteo_without_pressure_falls_back_to_nasa_power(self):
        yesterday = date.today() - timedelta(days=1)
        daily = _daily([yesterday, date.today()], FULL_VALUES)
        daily["surface_pressure_mean"][0] = None

        def fake_get(url, params, timeout):
            if url == NASA_POWER_URL:
                return _nasa_response(yesterday)
            return _response({"daily": daily})

        with patch("app.ingestion.climate.httpx.get", side_effect=fake_get) as get, \
             self.assertLogs("app.ingestion.climate", "WARNING") as logs:
            climate = get_climate_data(-10.0, -60.0, yesterday)

        self.assertEqual(get.call_count, 2)  # sin reintentos: la respuesta llegó, la fila es inválida
        self.assertIn("pressure_kpa", logs.output[0])
        self.assertEqual(climate.pressure_kpa, 93.1)  # valor de NASA POWER
        self.assertIsNone(climate.eto_reference_mm)


if __name__ == "__main__":
    unittest.main()
