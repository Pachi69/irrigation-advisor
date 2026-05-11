"""Configuración de APScheduler para jobs automáticos."""
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.jobs.recommendation_job import generate_daily_recommendations
from app.jobs.notification_job import send_daily_recommendation_notifications
from app.jobs.alerts_job import generate_climate_alerts

MENDOZA_TZ = ZoneInfo("America/Argentina/Mendoza")

scheduler = BackgroundScheduler(timezone=MENDOZA_TZ)

scheduler.add_job(
    generate_daily_recommendations,
    trigger=CronTrigger(hour=0, minute=1, timezone=MENDOZA_TZ),
    id="daily_recommendations",
    name="Recomendaciones diarias - 00:01hs Mendoza",
    replace_existing=True,
)

scheduler.add_job(
    send_daily_recommendation_notifications,
    trigger=CronTrigger(hour=8, minute=0, timezone=MENDOZA_TZ),
    id="daily_notifications",
    name="Notificaciones push recomendación - 08hs Mendoza",
    replace_existing=True,
)

scheduler.add_job(
    generate_climate_alerts,
    trigger=CronTrigger(hour="*/6", timezone=MENDOZA_TZ),
    id="climate_alerts",
    name="Alertas climáticas - cada 6hs",
    replace_existing=True,
)