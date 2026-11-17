from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.endpoints import health, jwks
from app.api.v1.routers import api_router
from app.core.tokens import load_private_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_private_key()  # fail at startup, not on the first login
    yield


app = FastAPI(
    title="Auth API",
    version="1.0.0",
    openapi_url="/api/v1/auth/openapi.json",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(jwks.router)
app.include_router(api_router, prefix="/api/v1")
