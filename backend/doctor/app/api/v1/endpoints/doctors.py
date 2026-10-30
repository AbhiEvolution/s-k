from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.doctor import DoctorCreate, DoctorResponse
from app.services.doctor import DoctorService
from app.core.dependencies import get_current_doctor
from app.models.doctor import Doctor
from db.database import get_db

router = APIRouter(
  prefix="/doctors",
  tags=["Doctors"], 
)

@router.post("/register", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def register_doctor(data: DoctorCreate, db: Session = Depends(get_db)):
  try:
    return DoctorService.create_doctor(db, data)
  except ValueError as exc:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail=str(exc)
    )

@router.get("/me", response_model=DoctorResponse)
def get_my_profile(current_doctor: Doctor = Depends(get_current_doctor)):
  return current_doctor
