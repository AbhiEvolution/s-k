
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_doctor_id
from app.schemas.patients import PatientCreate, PatientResponse
from app.services.patient import PatientService
from db.database import get_db

router = APIRouter(
  prefix="/patients",
  tags=["patients"],
)

patient_service = PatientService()

@router.post( "",response_model=PatientResponse, status_code=status.HTTP_201_CREATED,)
def new_patient( request: PatientCreate, db: Session = Depends(get_db), doctor_id: int = Depends(get_current_doctor_id)) -> PatientResponse:
  return patient_service.create_patient(db=db, request=request, doctor_id=doctor_id)


@router.get("", response_model=list[PatientResponse])
def get_all_patients(db: Session = Depends(get_db),skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=100),doctor_id: int = Depends(get_current_doctor_id),) -> list[PatientResponse]:
  return patient_service.get_all_patients(db=db,doctor_id=doctor_id, skip=skip, limit=limit)


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db), doctor_id: int = Depends(get_current_doctor_id)) -> PatientResponse:
  return patient_service.get_patient(db=db, patient_id=patient_id,doctor_id=doctor_id)


@router.put(
  "/{patient_id}",
  response_model=PatientResponse,
)
def edit_patient(patient_id: int, request: PatientCreate, db: Session = Depends(get_db), doctor_id: int = Depends(get_current_doctor_id)) -> PatientResponse:
  return patient_service.update_patient(db=db,patient_id=patient_id, doctor_id=doctor_id,request=request,)


@router.delete("/{patient_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db), doctor_id: int = Depends(get_current_doctor_id)) -> Response:
  patient_service.delete_patient(db=db, patient_id=patient_id, doctor_id=doctor_id,)
  return Response(status_code=status.HTTP_204_NO_CONTENT)
