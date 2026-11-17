from fastapi import FastAPI

from app.api.v1.endpoints import health
from app.api.v1.routers import api_router

app = FastAPI(
    title="Clinic API",
    version="1.0.0",
    openapi_url="/api/v1/clinics/openapi.json",
)

app.include_router(health.router)
app.include_router(api_router, prefix="/api/v1")
