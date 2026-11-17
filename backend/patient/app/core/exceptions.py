from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.clinic_client import ClinicServiceUnavailableError, NotClinicMemberError


class PatientNotFoundError(Exception):
  def __init__(self, patient_id: int):
    self.patient_id = patient_id
    super().__init__(f"Patient {self.patient_id} not found")


async def patient_not_found_handler(request: Request, exc: PatientNotFoundError) -> JSONResponse:
  return JSONResponse(status_code=404, content={"detail": str(exc)})


async def not_member_handler(request: Request, exc: NotClinicMemberError) -> JSONResponse:
  return JSONResponse(status_code=403, content={"detail": "You are not a member of that clinic"})


async def clinic_unavailable_handler(
  request: Request, exc: ClinicServiceUnavailableError
) -> JSONResponse:
  return JSONResponse(status_code=503, content={"detail": "Clinic service unavailable"})
