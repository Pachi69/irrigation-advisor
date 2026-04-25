from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.auth.routes import router as auth_router
from app.api.fields import router as field_router
from app.api.admin import router as admin_router
from app.api.climate import router as climate_router
from app.api.recommendation import router as recommendation_router
from app.jobs.scheduler import scheduler

import logging
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    logger.info("APScheduler iniciado")
    yield
    scheduler.shutdown()
    logger.info("APScheduler detenido")

app = FastAPI(
    title="Irrigation Advisor API",
    version="0.1.0",
    docs_url="/docs" if settings.environment == "development" else None,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.frontend_url.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(field_router)
app.include_router(admin_router)
app.include_router(climate_router)
app.include_router(recommendation_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}