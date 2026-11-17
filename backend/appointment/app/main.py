from fastapi import FastAPI

from app.api.v1.endpoints import health
from app.api.v1.routers import api_router
from app.core.exceptions import register_exception_handlers

app = FastAPI(
    title="Appointments API",
    version="1.0.0",
    openapi_url="/api/v1/appointments/openapi.json",
)

app.include_router(health.router)
app.include_router(api_router, prefix="/api/v1")
register_exception_handlers(app)
