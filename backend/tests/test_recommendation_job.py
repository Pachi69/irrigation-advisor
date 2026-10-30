"""Pruebas del job diario de recomendaciones ante la falla de un sector, sin red.

Clima, pronóstico e imágenes se reemplazan por dobles. Verifican que si un
sector falla (por ejemplo, sin pronóstico) el job sigue con los demás, que el
sector fallido no queda marcado como calculado y que al día siguiente el
backfill recupera el día perdido con el mismo déficit que si no hubiera fallado.
"""
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from app.jobs.recommendation_job import generate_daily_recommendations
from app.models.daily_water_balance import DailyWaterBalance
from app.models.enums import UrgencyLevel
from app.models.sector import Sector
from tests._support import (
    LATITUDE, climate_day, climate_range, forecast_days,
    make_field, make_sector, make_user, new_session, reset_database,
)

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
SEED_DATE = YESTERDAY - timedelta(days=1)  # último día con balance de los dos sectores
SEED_DEFICIT_MM = 10.0
NO_FORECAST_LATITUDE = LATITUDE - 1.0


class _Tomorrow(date):
    """`date` cuyo `today()` es mañana, para correr el job del día siguiente."""

    @classmethod
    def today(cls):
        return TODAY + timedelta(days=1)


def _forecast(latitude, longitude, days):
    if latitude == NO_FORECAST_LATITUDE:
        raise RuntimeError("Open-Meteo no respondió tras 3 intentos")
    return forecast_days(TODAY, days)


class TestRecommendationJob(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.db = new_session()
        user = make_user(self.db)
        failing_field = make_field(self.db, user)
        failing_field.latitude = NO_FORECAST_LATITUDE
        sector = dict(last_deficit_mm=SEED_DEFICIT_MM, last_deficit_date=SEED_DATE)
        self.failing = make_sector(self.db, failing_field, name="Sin pronóstico", **sector)
        self.healthy = make_sector(self.db, make_field(self.db, user), name="Con pronóstico", **sector)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def _run_job(self, tomorrow: bool = False, forecast_fails: bool = True) -> list[str]:
        """Corre el job con dobles de clima, pronóstico e imágenes; devuelve su log."""
        forecast = _forecast if forecast_fails else (lambda latitude, longitude, days: forecast_days(TODAY, days))
        with patch("app.services.recommendation.get_forecast", side_effect=forecast), \
             patch("app.services.water_balance.get_climate_data", side_effect=lambda lat, lon, day: climate_day(day)), \
             patch("app.services.recommendation.get_climate_data_for_range",
                   side_effect=lambda lat, lon, start, end: climate_range(start, end)), \
             patch("app.services.recommendation.fetch_latest_s2"), \
             patch("app.services.recommendation.prefetch_s2_for_range"), \
             patch("app.services.recommendation.DateType", _Tomorrow if tomorrow else date), \
             self.assertLogs("app.jobs.recommendation_job", "INFO") as logs:
            generate_daily_recommendations()
        self.db.expire_all()
        return logs.output

    def _balance(self, sector: Sector, day: date) -> DailyWaterBalance | None:
        return (
            self.db.query(DailyWaterBalance)
            .filter(DailyWaterBalance.sector_id == sector.id, DailyWaterBalance.date == day)
            .first()
        )

    def test_failing_sector_does_not_stop_the_others(self):
        logs = self._run_job()

        healthy = self._balance(self.healthy, YESTERDAY)
        assert healthy is not None and healthy.recommendation is not None
        self.assertGreater(healthy.water_deficit_mm, SEED_DEFICIT_MM)
        self.assertIsNone(self._balance(self.failing, YESTERDAY))
        self.assertEqual(self.failing.last_deficit_date, SEED_DATE)  # no avanza: el día queda pendiente
        self.assertEqual(self.failing.last_deficit_mm, SEED_DEFICIT_MM)
        self.assertTrue(any(f"Error procesando sector {self.failing.id}" in line for line in logs))
        self.assertIn("ok: 1, errores: 1", logs[-1])

    def test_next_day_recovers_the_missing_day(self):
        self._run_job()
        logs = self._run_job(tomorrow=True, forecast_fails=False)

        self.assertIn("ok: 2, errores: 0", logs[-1])
        recovered = self._balance(self.failing, YESTERDAY)
        reference = self._balance(self.healthy, YESTERDAY)
        assert recovered is not None and recovered.recommendation is not None and reference is not None
        self.assertEqual(recovered.water_deficit_mm, reference.water_deficit_mm)
        self.assertEqual(recovered.recommendation.urgency, UrgencyLevel.low)  # día recuperado por backfill

        failing_today = self._balance(self.failing, TODAY)
        healthy_today = self._balance(self.healthy, TODAY)
        assert failing_today is not None and healthy_today is not None
        self.assertEqual(failing_today.water_deficit_mm, healthy_today.water_deficit_mm)
        self.assertGreater(failing_today.water_deficit_mm, recovered.water_deficit_mm)
        self.assertEqual(self.failing.last_deficit_date, TODAY)


if __name__ == "__main__":
    unittest.main()
