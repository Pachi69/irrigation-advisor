from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.auth.routes import router as auth_router
from app.api.fields import router as field_router

app = FastAPI(
    title="Irrigation Advisor API",
    version="0.1.0",
    docs_url="/docs" if settings.environment == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(field_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}