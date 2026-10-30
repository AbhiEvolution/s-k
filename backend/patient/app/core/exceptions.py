from fastapi import Request
from fastapi.responses import JSONResponse

class PatientNotFoundError(Exception):
  def __init__(self, patient_id: int):
    self.patient_id = patient_id
    super().__init__(f"Patient {self.patient_id} not found")

async def patient_not_found_handler(
  request: Request,
  exc: PatientNotFoundError,
) -> JSONResponse:
  return JSONResponse(
    status_code=404,
    content={"detail": str(exc)},
  )