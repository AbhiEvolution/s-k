from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import health
from app.api.v1.routers import api_router
from app.core.clinic_client import ClinicServiceUnavailableError, NotClinicMemberError
from app.core.exceptions import (
  PatientNotFoundError,
  clinic_unavailable_handler,
  not_member_handler,
  patient_not_found_handler,
)

app = FastAPI(
  title="Patients API",
  version="2.0.0",
  openapi_url="/api/v1/patients/openapi.json",
)
app.include_router(health.router)
app.include_router(api_router, prefix="/api/v1")

app.add_exception_handler(PatientNotFoundError, patient_not_found_handler)
app.add_exception_handler(NotClinicMemberError, not_member_handler)
app.add_exception_handler(ClinicServiceUnavailableError, clinic_unavailable_handler)

app.add_middleware(
  CORSMiddleware,
  allow_origins=['http://localhost:5173'],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)
