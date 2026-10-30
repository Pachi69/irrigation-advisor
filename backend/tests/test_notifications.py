"""Pruebas de las notificaciones push de la recomendación diaria, sin red.

El job se prueba con el envío reemplazado por un doble y la hora de Mendoza
fijada por la prueba: verifican la hora elegida, la frecuencia, que solo se
avise si ayer hay lámina a regar y el texto del mensaje. El servicio push se
prueba con `webpush` reemplazado: una suscripción muerta (404/410) se borra y
una falla pasajera (5xx o corte de red) se conserva para reintentar.
"""
import unittest
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import requests
from pywebpush import WebPushException

from app.jobs.notification_job import (
    DEFAULT_NOTIFICATION_HOUR, MENDOZA_TZ, _amount_text, send_daily_recommendation_notifications,
)
from app.models.daily_water_balance import DailyWaterBalance
from app.models.enums import ConfidenceLevel, KcSource, PhenologicalStage, UrgencyLevel
from app.models.push_subscription import PushSubscription
from app.models.recommendation import Recommendation
from app.models.sector import Sector
from app.services.push import send_push_to_user
from tests._support import make_field, make_sector, make_user, new_session, reset_database

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)


class TestNotificationJob(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.db = new_session()
        self.field = make_field(self.db, make_user(self.db))

    def tearDown(self):
        self.db.close()

    def _sector(self, name: str = "Sector de prueba", **kwargs) -> Sector:
        return make_sector(self.db, self.field, name=name, **kwargs)

    def _recommendation(self, sector: Sector, mm: float = 8.0, day: date = YESTERDAY, **kwargs) -> None:
        balance = DailyWaterBalance(
            sector_id=sector.id, date=day, eto_mm=6.0, kc=0.6, kc_source=KcSource.tabular,
            etc_mm=3.6, water_deficit_mm=mm, ks=1.0, phenological_stage=PhenologicalStage.mid,
            precipitation_mm=0.0, taw_mm=100.0,
        )
        balance.recommendation = Recommendation(
            recommended_irrigation_mm=mm, urgency=kwargs.pop("urgency", UrgencyLevel.high),
            reason="Prueba", confidence=ConfidenceLevel.high, **kwargs,
        )
        self.db.add(balance)

    def _run_at(self, hour: int, sent: int = 1):
        """Corre el job como si en Mendoza fueran las `hour` horas; devuelve el doble del envío."""
        self.db.commit()
        now = datetime.combine(TODAY, time(hour), tzinfo=MENDOZA_TZ)
        with patch("app.jobs.notification_job.datetime") as clock, \
             patch("app.jobs.notification_job.send_push_to_user", return_value=sent) as send, \
             self.assertLogs("app.jobs.notification_job", "INFO") as logs:
            clock.now.return_value = now
            send_daily_recommendation_notifications()
        self.logs = logs.output
        self.db.expire_all()
        return send

    def test_sends_only_at_the_chosen_hour(self):
        early = self._sector("Temprano", notification_hour=time(7, 0))
        default = self._sector("Sin hora")
        self._recommendation(early)
        self._recommendation(default)

        self.assertEqual(DEFAULT_NOTIFICATION_HOUR, 8)
        self.assertEqual(self._run_at(6).call_count, 0)
        send = self._run_at(7)
        self.assertEqual(send.call_count, 1)
        self.assertIn("Temprano", send.call_args.kwargs["title"])
        send = self._run_at(8)
        self.assertEqual(send.call_count, 1)
        self.assertIn("Sin hora", send.call_args.kwargs["title"])

    def test_frequency_is_counted_from_the_last_notification(self):
        recent = self._sector("Hace 2 días", notification_frequency_days=3, last_notification_date=TODAY - timedelta(days=2))
        due = self._sector("Hace 3 días", notification_frequency_days=3, last_notification_date=TODAY - timedelta(days=3))
        self._recommendation(recent)
        self._recommendation(due)

        send = self._run_at(DEFAULT_NOTIFICATION_HOUR)

        self.assertEqual(send.call_count, 1)
        self.assertIn("Hace 3 días", send.call_args.kwargs["title"])
        self.assertEqual(due.last_notification_date, TODAY)
        self.assertEqual(recent.last_notification_date, TODAY - timedelta(days=2))
        self.assertIn("sin_frecuencia: 1", self.logs[-1])

    def test_needs_yesterdays_recommendation_with_water_to_apply(self):
        self._sector("Sin balance")
        old = self._sector("Balance viejo")
        self._recommendation(old, day=TODAY - timedelta(days=2))
        zero = self._sector("Lámina cero")
        self._recommendation(zero, mm=0.0)
        self._recommendation(self._sector("Con lámina"))

        send = self._run_at(DEFAULT_NOTIFICATION_HOUR)

        self.assertEqual(send.call_count, 1)
        self.assertIn("Con lámina", send.call_args.kwargs["title"])
        self.assertIn("sin_rec: 2 lamina0: 1", self.logs[-1])

    def test_failed_send_does_not_count_as_notified(self):
        sector = self._sector()
        self._recommendation(sector)

        self._run_at(DEFAULT_NOTIFICATION_HOUR, sent=0)
        self.assertIsNone(sector.last_notification_date)
        self.assertIn("sin envio: 1", self.logs[-1])
        self.assertEqual(self._run_at(DEFAULT_NOTIFICATION_HOUR).call_count, 1)  # se reintenta
        self.assertEqual(sector.last_notification_date, TODAY)

    def test_message_text(self):
        sector = self._sector()
        self._recommendation(sector, time_min=90.0, volume_m3=80.0)

        send = self._run_at(DEFAULT_NOTIFICATION_HOUR)

        send.assert_called_once()
        self.assertEqual(send.call_args.kwargs["user_id"], self.field.user_id)
        self.assertEqual(send.call_args.kwargs["title"], "Riego - Campo de prueba / Sector de prueba")
        self.assertEqual(send.call_args.kwargs["body"], "Regar 1 h 30 min de riego - Urgencia: Alta")

        amounts = {  # tiempo si hay caudal, si no volumen, si no lámina
            "45 min de riego": SimpleNamespace(recommended_irrigation_mm=8.0, time_min=45.0, volume_m3=80.0),
            "2 h de riego": SimpleNamespace(recommended_irrigation_mm=8.0, time_min=120.0, volume_m3=80.0),
            "80.0 m³": SimpleNamespace(recommended_irrigation_mm=8.0, time_min=None, volume_m3=80.0),
            "8.0 mm": SimpleNamespace(recommended_irrigation_mm=8.0, time_min=None, volume_m3=None),
        }
        for expected, rec in amounts.items():
            with self.subTest(expected=expected):
                self.assertEqual(_amount_text(rec), expected)


def _push_error(status_code: int) -> WebPushException:
    response = requests.Response()
    response.status_code = status_code
    response._content = b"respuesta del servicio push"
    return WebPushException(f"Push failed: {status_code}", response=response)


class TestPushService(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.db = new_session()
        self.user = make_user(self.db)

    def tearDown(self):
        self.db.close()

    def _subscribe(self, *names: str) -> None:
        for name in names:
            self.db.add(PushSubscription(
                user_id=self.user.id, endpoint=f"https://push.example.com/{name}", p256dh="clave", auth="secreto",
            ))
        self.db.commit()

    def _send(self, outcomes: dict[str, Exception | None]) -> int:
        """Envía al usuario; `outcomes` dice qué pasa con cada dispositivo (None = entregada)."""
        def fake_webpush(subscription_info, **kwargs):
            self.assertEqual(kwargs["timeout"], 10)
            error = outcomes[subscription_info["endpoint"].rsplit("/", 1)[1]]
            if error is not None:
                raise error

        with patch("app.services.push.webpush", side_effect=fake_webpush) as webpush, \
             self.assertLogs("app.services.push", "INFO"):
            sent = send_push_to_user(self.user.id, "Título", "Cuerpo", self.db)
        self.assertEqual(webpush.call_count, len(outcomes))
        return sent

    def _remaining(self) -> list[str]:
        return sorted(s.endpoint.rsplit("/", 1)[1] for s in self.db.query(PushSubscription).all())

    def test_dead_subscription_is_deleted_and_transient_error_is_kept(self):
        self._subscribe("celular", "vieja", "compu")
        sent = self._send({"celular": None, "vieja": _push_error(410), "compu": _push_error(503)})

        self.assertEqual(sent, 1)
        self.assertEqual(self._remaining(), ["celular", "compu"])

    def test_network_error_keeps_subscription_and_tries_the_rest(self):
        self._subscribe("celular", "compu")
        sent = self._send({"celular": requests.ConnectionError("sin red"), "compu": None})

        self.assertEqual(sent, 1)
        self.assertEqual(self._remaining(), ["celular", "compu"])


if __name__ == "__main__":
    unittest.main()
