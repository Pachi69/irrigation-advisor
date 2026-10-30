"""Pruebas de la detección del tipo de suelo con SoilGrids 2.0, sin red.

`httpx.Client` se reemplaza por un cliente con `MockTransport`: la consulta se
arma igual que en producción, pero la respuesta la da la prueba. Verifican la
conversión de g/kg a %, la clasificación USDA de las 12 texturas, el rechazo
de fracciones incompletas o inválidas y que una falla de la API no corta el
alta del campo (devuelve None y se reintenta en la siguiente actualización).
"""
import unittest
from unittest.mock import patch

import httpx

from app.ingestion.soil import SOILGRIDS_URL, get_soil_type_from_coords
from app.models.enums import SoilType
from app.services.sector import update_field_geo
from tests._support import (
    LATITUDE, LONGITUDE, make_field, make_sector, make_user, new_session, reset_database,
)

_REAL_CLIENT = httpx.Client

# Arena, limo y arcilla en % (suman 100), un punto dentro de cada clase USDA
TEXTURES = {
    SoilType.sand:            (92, 5, 3),
    SoilType.loamy_sand:      (80, 12, 8),
    SoilType.sandy_loam:      (65, 20, 15),
    SoilType.sandy_clay_loam: (60, 15, 25),
    SoilType.loam:            (40, 40, 20),
    SoilType.silt_loam:       (20, 65, 15),
    SoilType.silt:            (5, 90, 5),
    SoilType.clay_loam:       (30, 35, 35),
    SoilType.silty_clay_loam: (10, 55, 35),
    SoilType.sandy_clay:      (50, 5, 45),
    SoilType.silty_clay:      (5, 50, 45),
    SoilType.clay:            (20, 20, 60),
}


def _layers(sand: float | None, silt: float | None, clay: float | None) -> dict:
    """Respuesta de SoilGrids con las fracciones en g/kg."""
    values = {"sand": sand, "silt": silt, "clay": clay}
    return {"properties": {"layers": [
        {"name": name, "depths": [{"label": "0-5cm", "values": {"mean": value}}]}
        for name, value in values.items()
    ]}}


def _soilgrids(handler):
    """Reemplazo de `httpx.Client` que responde con `handler` en lugar de la red."""
    def client(timeout):
        return _REAL_CLIENT(transport=httpx.MockTransport(handler), timeout=timeout)
    return patch("app.ingestion.soil.httpx.Client", side_effect=client)


def _answer(payload: dict, status_code: int = 200):
    return _soilgrids(lambda request: httpx.Response(status_code, json=payload))


class TestSoilGridsQuery(unittest.TestCase):

    def test_response_to_soil_type(self):
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, json=_layers(650, 200, 150))

        with _soilgrids(handler), self.assertLogs("app.ingestion.soil", "INFO") as logs:
            soil = get_soil_type_from_coords(LATITUDE, LONGITUDE)

        self.assertEqual(soil, SoilType.sandy_loam)
        self.assertIn("sand=65.0% silt=20.0% clay=15.0%", logs.output[0])  # g/kg -> %
        params = requests[0].url.params
        self.assertEqual(str(requests[0].url.copy_with(query=None)), SOILGRIDS_URL)
        self.assertEqual(params.get_list("property"), ["clay", "silt", "sand"])
        self.assertEqual(params["depth"], "0-5cm")
        self.assertEqual(params["value"], "mean")

    def test_every_usda_texture_class(self):
        self.assertEqual(set(TEXTURES), set(SoilType))
        for expected, (sand, silt, clay) in TEXTURES.items():
            with self.subTest(soil=expected.value), \
                 _answer(_layers(sand * 10, silt * 10, clay * 10)), \
                 self.assertLogs("app.ingestion.soil", "INFO"):
                self.assertEqual(get_soil_type_from_coords(LATITUDE, LONGITUDE), expected)

    def test_incomplete_or_invalid_fractions_return_none(self):
        with _answer(_layers(400, 400, None)), \
             self.assertLogs("app.ingestion.soil", "WARNING") as logs:
            self.assertIsNone(get_soil_type_from_coords(LATITUDE, LONGITUDE))
        self.assertIn("fracciones incompletas", logs.output[0])

        with _answer(_layers(300, 250, 150)), \
             self.assertLogs("app.ingestion.soil", "WARNING") as logs:  # suman 70 %
            self.assertIsNone(get_soil_type_from_coords(LATITUDE, LONGITUDE))
        self.assertIn("total=70.0%", logs.output[0])

    def test_api_failure_returns_none(self):
        def timeout(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("tiempo agotado", request=request)

        failures = {
            "error HTTP": _answer({}, status_code=503),
            "tiempo agotado": _soilgrids(timeout),
            "respuesta sin capas": _answer({"properties": {}}),
        }
        for case, double in failures.items():
            with self.subTest(case=case), double, \
                 self.assertLogs("app.ingestion.soil", "WARNING") as logs:
                self.assertIsNone(get_soil_type_from_coords(LATITUDE, LONGITUDE))
                self.assertIn("SoilGrids no disponible", logs.output[0])


class TestFieldGeo(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.db = new_session()
        self.field = make_field(self.db, make_user(self.db), soil_type=None)
        self.field.elevation_m = None
        make_sector(self.db, self.field)
        self.db.refresh(self.field)

    def tearDown(self):
        self.db.close()

    def test_soil_is_detected_once_and_retried_after_a_failure(self):
        detections = [None, SoilType.loam]
        with patch("app.services.sector.get_soil_type_from_coords", side_effect=detections) as soil, \
             patch("app.ingestion.climate.get_elevation", return_value=700.0) as elevation:
            update_field_geo(self.field, self.db)  # SoilGrids falla: el campo queda sin suelo
            self.assertIsNone(self.field.soil_type)
            update_field_geo(self.field, self.db)  # se reintenta en la siguiente actualización
            update_field_geo(self.field, self.db)  # ya tiene suelo: no se consulta más

        self.assertEqual(self.field.soil_type, SoilType.loam)
        self.assertEqual(soil.call_count, 2)
        elevation.assert_called_once()
        assert self.field.latitude is not None and self.field.longitude is not None
        self.assertAlmostEqual(self.field.latitude, LATITUDE + 0.0005)  # centroide del polígono
        self.assertAlmostEqual(self.field.longitude, LONGITUDE + 0.0005)
        soil.assert_called_with(self.field.latitude, self.field.longitude)


if __name__ == "__main__":
    unittest.main()
