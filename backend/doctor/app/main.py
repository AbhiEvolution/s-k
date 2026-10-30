from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import api_router

app = FastAPI(title="Doctors API", version="1.0.0")
app.include_router(api_router, prefix="/api/v1")

app.add_middleware(
  CORSMiddleware,
  allow_origins=['http://localhost:5173'],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)