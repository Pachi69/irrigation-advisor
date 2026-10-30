"""Pruebas de flujo completo sobre la API, sin red.

Recorren los endpoints como lo haría el frontend: registro, ingreso, alta de
campo y sector, aprobación del administrador, recomendación, confirmación del
riego y suscripción push. Clima, pronóstico, imágenes, elevación, suelo y
envío push se reemplazan por dobles. El cliente se crea sin `with` para no
arrancar el planificador de tareas.
"""
import unittest
from contextlib import ExitStack
from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.jobs.notification_job import DEFAULT_NOTIFICATION_HOUR, MENDOZA_TZ, send_daily_recommendation_notifications
from app.main import app
from app.models import User, UserRole
from app.models.enums import SoilType
from tests._support import ELEVATION_M, POLYGON, climate_day, climate_range, forecast_days, new_session, reset_database

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
SATURATION_DATE = TODAY - timedelta(days=60)  # Dr = 0 ese día; el balance arranca el día siguiente
PASSWORD = "clave-de-prueba"


class TestApiFlow(unittest.TestCase):

    def setUp(self):
        reset_database()
        self.client = TestClient(app)
        self.external = ExitStack()
        doubles = {
            "app.ingestion.climate.get_elevation": dict(return_value=ELEVATION_M),
            "app.services.sector.get_soil_type_from_coords": dict(return_value=SoilType.sand),
            "app.services.recommendation.get_forecast": dict(side_effect=lambda lat, lon, days: forecast_days(TODAY, days)),
            "app.services.water_balance.get_climate_data": dict(side_effect=lambda lat, lon, day: climate_day(day)),
            "app.services.recommendation.get_climate_data_for_range":
                dict(side_effect=lambda lat, lon, start, end: climate_range(start, end)),
            "app.services.recommendation.fetch_latest_s2": {},
            "app.services.recommendation.prefetch_s2_for_range": {},
        }
        for target, kwargs in doubles.items():
            self.external.enter_context(patch(target, **kwargs))
        self.producer = self._signup("productor@example.com")
        self.admin = self._signup("admin@example.com", role=UserRole.admin)

    def tearDown(self):
        self.external.close()

    def _signup(self, email: str, role: UserRole = UserRole.producer) -> dict[str, str]:
        """Registra e ingresa un usuario por la API; devuelve el encabezado de autenticación."""
        response = self.client.post("/auth/register", json={"name": "Usuario de prueba", "email": email, "password": PASSWORD})
        self.assertEqual(response.status_code, 201, response.text)
        if role != UserRole.producer:  # no hay endpoint para dar el rol de administrador
            with new_session() as db:
                db.query(User).filter(User.email == email).update({"role": role})
                db.commit()
        response = self.client.post("/auth/login", json={"email": email, "password": PASSWORD})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def _new_sector(self) -> int:
        """Alta de campo y sector con polígono por el productor; devuelve el id del sector."""
        field = self.client.post("/fields", json={"name": "Campo de prueba"}, headers=self.producer)
        self.assertEqual(field.status_code, 201, field.text)
        sector = self.client.post(
            f"/fields/{field.json()['id']}/sectors", headers=self.producer,
            json={"name": "Malbec norte", "crop_type": "vine", "flow_rate_ls_ha": 10.0,
                  "last_saturation_date": SATURATION_DATE.isoformat(), "polygon_geojson": POLYGON},
        )
        self.assertEqual(sector.status_code, 201, sector.text)
        return sector.json()["id"]

    def _approved_sector(self) -> int:
        sector_id = self._new_sector()
        response = self.client.post(f"/admin/sectors/{sector_id}/approve", headers=self.admin)
        self.assertEqual(response.status_code, 200, response.text)
        return sector_id

    def _deficits(self, sector_id: int) -> dict[str, float]:
        history = self.client.get(f"/sectors/{sector_id}/recommendations", headers=self.producer).json()
        return {item["date"]: item["water_deficit_mm"] for item in history}

    def test_from_signup_to_first_recommendation(self):
        me = self.client.get("/auth/me", headers=self.producer)
        self.assertEqual(me.json()["role"], "producer")

        sector_id = self._new_sector()
        field = self.client.get("/fields", headers=self.producer).json()[0]
        self.assertEqual(field["soil_type"], "sand")  # suelo y elevación al cargar el polígono
        self.assertEqual(field["elevation_m"], ELEVATION_M)
        sector = self.client.get(f"/sectors/{sector_id}", headers=self.producer).json()
        self.assertEqual(sector["status"], "pending")
        self.assertGreater(sector["area_ha"], 0)
        self.assertEqual(self.client.get(f"/sectors/{sector_id}/recommendation", headers=self.producer).status_code, 409)

        approved = self.client.post(f"/admin/sectors/{sector_id}/approve", headers=self.admin)
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()["status"], "active")

        recommendation = self.client.get(f"/sectors/{sector_id}/recommendation", headers=self.producer)
        self.assertEqual(recommendation.status_code, 200, recommendation.text)
        self.assertEqual(recommendation.json()["date"], YESTERDAY.isoformat())
        self.assertGreater(recommendation.json()["recommended_irrigation_mm"], 0)

        deficits = self._deficits(sector_id)  # del día siguiente a la saturación hasta ayer
        days = [SATURATION_DATE + timedelta(days=i) for i in range(1, 60)]
        self.assertEqual(sorted(deficits), [day.isoformat() for day in days])
        values = [deficits[day.isoformat()] for day in days]
        self.assertEqual(values, sorted(values))  # sin lluvia ni riego el déficit solo crece

    def test_confirmed_irrigation_recomputes_the_balance(self):
        sector_id = self._approved_sector()
        url = f"/sectors/{sector_id}"
        before = self._deficits(sector_id)
        pending = self.client.get(f"{url}/pending-confirmations", headers=self.producer).json()
        latest = pending[0]
        self.assertEqual(latest["date"], YESTERDAY.isoformat())

        irrigation_day = TODAY - timedelta(days=3)
        payload = {"irrigation_date": irrigation_day.isoformat(), "applied_time_min": 600}
        confirm = f"{url}/recommendations/{latest['recommendation_id']}/confirm"
        confirmed = self.client.post(confirm, json=payload, headers=self.producer)
        self.assertEqual(confirmed.status_code, 201, confirmed.text)
        self.assertGreater(confirmed.json()["applied_irrigation_mm"], 0)

        after = self._deficits(sector_id)
        day_before = (irrigation_day - timedelta(days=1)).isoformat()
        self.assertEqual(after[day_before], before[day_before])  # antes del riego no cambia
        for day in (irrigation_day, YESTERDAY):
            self.assertLess(after[day.isoformat()], before[day.isoformat()])

        pending_ids = [item["recommendation_id"] for item in self.client.get(f"{url}/pending-confirmations", headers=self.producer).json()]
        self.assertNotIn(latest["recommendation_id"], pending_ids)
        self.assertEqual(self.client.post(confirm, json=payload, headers=self.producer).status_code, 400)  # ya confirmada
        future = dict(payload, irrigation_date=(TODAY + timedelta(days=1)).isoformat())
        other = f"{url}/recommendations/{pending[1]['recommendation_id']}/confirm"
        self.assertEqual(self.client.post(other, json=future, headers=self.producer).status_code, 400)

    def test_access_is_limited_to_the_owner_and_the_admin(self):
        sector_id = self._new_sector()
        neighbor = self._signup("vecino@example.com")
        approve = f"/admin/sectors/{sector_id}/approve"

        self.assertIn(self.client.get(f"/sectors/{sector_id}").status_code, (401, 403))  # sin sesión
        self.assertEqual(self.client.get(f"/sectors/{sector_id}", headers=neighbor).status_code, 404)
        self.assertEqual(self.client.post(approve, headers=self.producer).status_code, 403)
        self.assertEqual(self.client.post(approve, headers=self.admin).status_code, 200)
        self.assertEqual(self.client.post(approve, headers=self.admin).status_code, 409)
        self.assertEqual(self.client.get(f"/sectors/{sector_id}/recommendation", headers=neighbor).status_code, 404)

    def test_subscribed_device_gets_the_daily_notification(self):
        self._approved_sector()
        subscription = {"endpoint": "https://push.example.com/celular", "p256dh": "clave", "auth": "secreto"}
        response = self.client.post("/push/subscribe", json=subscription, headers=self.producer)
        self.assertEqual(response.status_code, 201, response.text)

        with patch("app.services.push.webpush") as webpush, \
             patch("app.jobs.notification_job.datetime") as clock:
            clock.now.return_value = datetime.combine(TODAY, time(DEFAULT_NOTIFICATION_HOUR), tzinfo=MENDOZA_TZ)
            send_daily_recommendation_notifications()

        webpush.assert_called_once()
        self.assertEqual(webpush.call_args.kwargs["subscription_info"]["endpoint"], subscription["endpoint"])
        self.assertIn("Malbec norte", webpush.call_args.kwargs["data"])

    def test_sector_without_polygon_cannot_be_approved(self):
        field = self.client.post("/fields", json={"name": "Campo de prueba"}, headers=self.producer).json()
        sector = self.client.post(f"/fields/{field['id']}/sectors", json={"name": "Sin dibujar", "crop_type": "vine"},
                                  headers=self.producer).json()

        response = self.client.post(f"/admin/sectors/{sector['id']}/approve", headers=self.admin)

        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["detail"], "El sector debe tener un polígono antes de aprobar")
        self.assertEqual(self.client.get(f"/sectors/{sector['id']}", headers=self.producer).json()["status"], "pending")



if __name__ == "__main__":
    unittest.main()
