"""Configracion de APScheduler para jobs automaticos."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.jobs.recommendation_job import generate_daily_recommendations

scheduler = BackgroundScheduler(timezone="America/Argentina/Mendoza")

scheduler.add_job(
    generate_daily_recommendations,
    trigger=CronTrigger(hour=22, minute=0),
    id="daily_recommendations",
    name="Recomendaciones diarias - 22hs Mendoza",
    replace_existing=True,
)