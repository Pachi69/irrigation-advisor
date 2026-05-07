"""Configuración de APScheduler para jobs automáticos."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.jobs.recommendation_job import generate_daily_recommendations
from app.jobs.notification_job import send_daily_recommendation_notifications
from app.jobs.alerts_job import generate_climate_alerts

scheduler = BackgroundScheduler(timezone="America/Argentina/Mendoza")

scheduler.add_job(
    generate_daily_recommendations,
    trigger=CronTrigger(hour=0, minute=1),
    id="daily_recommendations",
    name="Recomendaciones diarias - 00:01hs Mendoza",
    replace_existing=True,
)

scheduler.add_job(
    send_daily_recommendation_notifications,
    trigger=CronTrigger(hour=8, minute=0),
    id="daily_notifications",
    name="Notificaciones push recomendación - 08hs Mendoza",
    replace_existing=True,
)

scheduler.add_job(
    generate_climate_alerts,
    trigger=CronTrigger(hour="*/6"),
    id="climate_alerts",
    name="Alertas climáticas - cada 6hs",
    replace_existing=True,
)