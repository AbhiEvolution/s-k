from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import health
from app.api.v1.routers import api_router

app = FastAPI(
    title="Doctors API",
    version="2.0.0",
    docs_url="/docs",
    openapi_url="/api/v1/doctors/openapi.json",
)

app.include_router(health.router)
app.include_router(api_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
