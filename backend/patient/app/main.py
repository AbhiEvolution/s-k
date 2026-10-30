from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 

from app.api.v1.routers import api_router
from app.core.exceptions import (PatientNotFoundError, patient_not_found_handler )

app = FastAPI(title="Patients API", version="1.0.0")
app.include_router(api_router, prefix="/api/v1")

app.add_exception_handler(
  PatientNotFoundError,
  patient_not_found_handler,
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=['http://localhost:5173'],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)