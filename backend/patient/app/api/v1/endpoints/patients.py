from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user, get_raw_token
from app.schemas.patients import PatientCreate, PatientResponse, PatientUpdate
from app.services.patient import PatientService
from db.database import get_db

router = APIRouter(
  prefix="/patients",
  tags=["patients"],
)

patient_service = PatientService()


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def new_patient(
  request: PatientCreate,
  db: Session = Depends(get_db),
  user: CurrentUser = Depends(get_current_user),
  token: str = Depends(get_raw_token),
) -> PatientResponse:
  return patient_service.create_patient(db=db, request=request, user_id=user.id, token=token)


@router.get("", response_model=list[PatientResponse])
def get_all_patients(
  clinic_id: int = Query(gt=0),
  skip: int = Query(default=0, ge=0),
  limit: int = Query(default=100, ge=1, le=100),
  db: Session = Depends(get_db),
  user: CurrentUser = Depends(get_current_user),
  token: str = Depends(get_raw_token),
) -> list[PatientResponse]:
  return patient_service.get_all_patients(
    db=db, clinic_id=clinic_id, user_id=user.id, token=token, skip=skip, limit=limit
  )


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
  patient_id: int,
  db: Session = Depends(get_db),
  user: CurrentUser = Depends(get_current_user),
  token: str = Depends(get_raw_token),
) -> PatientResponse:
  return patient_service.get_patient(db=db, patient_id=patient_id, user_id=user.id, token=token)


@router.put("/{patient_id}", response_model=PatientResponse)
def edit_patient(
  patient_id: int,
  request: PatientUpdate,
  db: Session = Depends(get_db),
  user: CurrentUser = Depends(get_current_user),
  token: str = Depends(get_raw_token),
) -> PatientResponse:
  return patient_service.update_patient(
    db=db, patient_id=patient_id, user_id=user.id, token=token, request=request
  )


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
  patient_id: int,
  db: Session = Depends(get_db),
  user: CurrentUser = Depends(get_current_user),
  token: str = Depends(get_raw_token),
) -> Response:
  patient_service.delete_patient(db=db, patient_id=patient_id, user_id=user.id, token=token)
  return Response(status_code=status.HTTP_204_NO_CONTENT)
