"""Pruebas de la imagen satelital vigente y del cliente de Earth Engine, sin red.

Earth Engine se reemplaza por un doble (`MagicMock`): no se prueba el cálculo
del NDVI en los servidores de GEE, sino cómo el sistema arma la consulta,
interpreta la respuesta y elige qué imagen usar cada día (carry-forward sin
límite de antigüedad y forward-fill de hasta 5 días en el hueco inicial).
"""
import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from app.ingestion.satellite import (
    LOOKBACK_DAYS, SatelliteIndices, get_satellite_indices, get_satellite_indices_for_range,
)
from app.models.satellite_record import SatelliteRecord
from app.services.satellite import (
    SAT_FORWARD_FILL_MAX_DAYS, fetch_latest_s2, get_satellite_data_for_date,
    get_satellite_data_for_range, prefetch_s2_for_range, select_image_date,
)
from tests._support import POLYGON, make_field, make_sector, make_user, new_session, reset_database

DAY = date(2026, 1, 15)


def _days(*offsets: int) -> list[date]:
    return [DAY + timedelta(days=o) for o in offsets]


def _latest_image_chain(ee: MagicMock) -> MagicMock:
    """Colección que devuelve la cadena de filtros de `get_satellite_indices`."""
    return (
        ee.ImageCollection.return_value
        .filterBounds.return_value.filterDate.return_value
        .filter.return_value.map.return_value.sort.return_value
    )


class TestSelectImageDate(unittest.TestCase):

    def test_carry_forward_has_no_age_limit(self):
        images = _days(-200, -40, 0, 10)
        self.assertEqual(select_image_date(images, DAY), DAY)
        self.assertEqual(select_image_date(images, DAY + timedelta(days=9)), DAY)
        self.assertEqual(select_image_date(images, DAY - timedelta(days=1)), DAY - timedelta(days=40))
        self.assertEqual(select_image_date(_days(-200), DAY), DAY - timedelta(days=200))

    def test_initial_gap_forward_fill_up_to_five_days(self):
        self.assertEqual(SAT_FORWARD_FILL_MAX_DAYS, 5)
        self.assertEqual(select_image_date(_days(5, 20), DAY), DAY + timedelta(days=5))
        self.assertIsNone(select_image_date(_days(6, 20), DAY))
        self.assertIsNone(select_image_date([], DAY))


class TestImageForEachDay(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.db = new_session()
        self.sector = make_sector(self.db, make_field(self.db, make_user(self.db)))

    def tearDown(self):
        self.db.close()

    def _store(self, *offsets: int) -> None:
        for image_date in _days(*offsets):
            self.db.add(SatelliteRecord(sector_id=self.sector.id, date=image_date, ndvi=0.40, cloud_cover_pct=5.0))
        self.db.flush()

    def test_range_uses_the_rule_day_by_day(self):
        self._store(3, 12)  # sin imagen previa: el hueco inicial depende de la primera imagen
        result = get_satellite_data_for_range(self.sector, DAY - timedelta(days=4), DAY + timedelta(days=13), self.db)

        image_dates = {day: image_date for day, (_, image_date) in result.items()}
        self.assertIsNone(image_dates[DAY - timedelta(days=4)])  # 7 días antes de la imagen
        self.assertIsNone(image_dates[DAY - timedelta(days=3)])  # 6 días antes
        self.assertEqual(image_dates[DAY - timedelta(days=2)], DAY + timedelta(days=3))  # 5 días: forward-fill
        self.assertEqual(image_dates[DAY + timedelta(days=11)], DAY + timedelta(days=3))  # carry-forward
        self.assertEqual(image_dates[DAY + timedelta(days=13)], DAY + timedelta(days=12))
        satellite, _ = result[DAY + timedelta(days=12)]
        assert satellite is not None
        self.assertEqual(satellite.ndvi, 0.40)

    def test_range_forward_fills_from_an_image_after_the_range(self):
        self._store(8)
        result = get_satellite_data_for_range(self.sector, DAY, DAY + timedelta(days=4), self.db)

        self.assertIsNone(result[DAY][1])  # 8 días antes de la imagen
        self.assertEqual(result[DAY + timedelta(days=3)][1], DAY + timedelta(days=8))  # 5 días antes

    def test_single_day_matches_range(self):
        self._store(-30, 3, 12)
        start, end = DAY - timedelta(days=35), DAY + timedelta(days=15)
        by_range = get_satellite_data_for_range(self.sector, start, end, self.db)

        for offset in range((end - start).days + 1):
            day = start + timedelta(days=offset)
            with self.subTest(day=day):
                self.assertEqual(get_satellite_data_for_date(self.sector, day, self.db), by_range[day])

    def test_fetch_latest_persists_once_and_tolerates_gee_failure(self):
        image_date = DAY - timedelta(days=2)
        without_thumb = SatelliteIndices(ndvi=0.45, cloud_cover_pct=8.0, image_date=image_date)
        with_thumb = SatelliteIndices(ndvi=0.45, cloud_cover_pct=8.0, image_date=image_date, thumbnail_png=b"png")
        effects = [without_thumb, with_thumb, RuntimeError("GEE caído")]
        with patch("app.services.satellite.get_satellite_indices", side_effect=effects) as get, \
             self.assertLogs("app.services.satellite", "INFO") as logs:
            for _ in effects:
                fetch_latest_s2(self.sector, DAY, self.db)

        get.assert_called_with(POLYGON, DAY)
        records = self.db.query(SatelliteRecord).all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].date, image_date)
        self.assertEqual(records[0].ndvi, 0.45)
        self.assertEqual(records[0].thumbnail_png, b"png")
        self.assertTrue(any("No se pudo obtener NDVI" in line for line in logs.output))

    def test_prefetch_looks_back_and_skips_stored_images(self):
        self._store(0)
        found = [SatelliteIndices(ndvi=0.40, cloud_cover_pct=3.0, image_date=d) for d in _days(-10, 0, 5)]
        with patch("app.services.satellite.get_satellite_indices_for_range", return_value=found) as get, \
             self.assertLogs("app.services.satellite", "INFO"):
            prefetch_s2_for_range(self.sector, DAY, DAY + timedelta(days=10), self.db)

        get.assert_called_once_with(POLYGON, DAY - timedelta(days=15), DAY + timedelta(days=10))
        stored = sorted(r.date for r in self.db.query(SatelliteRecord).all())
        self.assertEqual(stored, _days(-10, 0, 5))


class TestEarthEngineClient(unittest.TestCase):

    def test_latest_image_is_read_and_thumbnail_failure_is_tolerated(self):
        with patch("app.ingestion.satellite.ee") as ee, \
             patch("app.ingestion.satellite.requests.get", side_effect=OSError("sin red")), \
             self.assertLogs("app.ingestion.satellite", "INFO") as logs:
            collection = _latest_image_chain(ee)
            collection.size.return_value.getInfo.return_value = 2
            image = collection.first.return_value
            image.get.return_value.getInfo.return_value = 12.5
            ee.Date.return_value.format.return_value.getInfo.return_value = "2026-01-10"
            ndvi_band = image.normalizedDifference.return_value.rename.return_value
            ndvi_band.reduceRegion.return_value.getInfo.return_value = {"NDVI": 0.42}

            indices = get_satellite_indices(POLYGON, DAY)

        assert indices is not None
        self.assertEqual(indices.ndvi, 0.42)
        self.assertEqual(indices.cloud_cover_pct, 12.5)
        self.assertEqual(indices.image_date, date(2026, 1, 10))
        self.assertIsNone(indices.thumbnail_png)
        image.normalizedDifference.assert_called_once_with(["B8", "B4"])
        filter_date = ee.ImageCollection.return_value.filterBounds.return_value.filterDate
        filter_date.assert_called_once_with(
            (DAY - timedelta(days=LOOKBACK_DAYS)).isoformat(), DAY.isoformat(),
        )
        self.assertTrue(any("thumbnail" in line for line in logs.output))

    def test_no_image_or_cloudy_polygon_returns_none_and_errors_raise(self):
        with patch("app.ingestion.satellite.ee") as ee, \
             self.assertLogs("app.ingestion.satellite", "WARNING"):
            collection = _latest_image_chain(ee)
            collection.size.return_value.getInfo.return_value = 0
            self.assertIsNone(get_satellite_indices(POLYGON, DAY))

            collection.size.return_value.getInfo.return_value = 1
            collection.first.return_value.get.return_value.getInfo.return_value = 5.0
            ee.Date.return_value.format.return_value.getInfo.return_value = "2026-01-10"
            ndvi_band = collection.first.return_value.normalizedDifference.return_value.rename.return_value
            ndvi_band.reduceRegion.return_value.getInfo.return_value = {"NDVI": None}
            self.assertIsNone(get_satellite_indices(POLYGON, DAY))

            collection.size.return_value.getInfo.side_effect = Exception("cuota excedida")
            with self.assertRaisesRegex(RuntimeError, "GEE.*cuota excedida"):
                get_satellite_indices(POLYGON, DAY)

    def test_range_skips_cloudy_images_removes_duplicates_and_sorts(self):
        features = {"features": [
            {"properties": {"ndvi": 0.50, "cloud_cover_pct": 4.0, "image_date": "2026-01-20"}},
            {"properties": {"ndvi": None, "cloud_cover_pct": 2.0, "image_date": "2026-01-18"}},
            {"properties": {"ndvi": 0.40, "cloud_cover_pct": None, "image_date": "2026-01-05"}},
            {"properties": {"ndvi": 0.55, "cloud_cover_pct": 1.0, "image_date": "2026-01-20"}},
        ]}
        with patch("app.ingestion.satellite.ee") as ee, \
             self.assertLogs("app.ingestion.satellite", "INFO"):
            filtered = ee.ImageCollection.return_value.filterBounds.return_value.filterDate
            filtered.return_value.filter.return_value.map.return_value.map.return_value.getInfo.return_value = features

            result = get_satellite_indices_for_range(POLYGON, date(2026, 1, 1), date(2026, 1, 31))

        filtered.assert_called_once_with("2026-01-01", "2026-02-01")  # filterDate excluye el último día
        self.assertEqual([r.image_date for r in result], [date(2026, 1, 5), date(2026, 1, 20)])
        self.assertEqual([r.ndvi for r in result], [0.40, 0.50])  # el duplicado conserva la primera
        self.assertEqual(result[0].cloud_cover_pct, 0.0)
        self.assertTrue(all(r.thumbnail_png is None for r in result))


if __name__ == "__main__":
    unittest.main()
