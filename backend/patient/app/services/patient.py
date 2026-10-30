from sqlalchemy.orm import Session

from app.repositories.patients import PatientRepository
from app.schemas.patients import PatientCreate, PatientResponse
from app.core.exceptions import PatientNotFoundError

class PatientService:
  def __init__(self):
    self.repository = PatientRepository()

  def create_patient(self,db: Session, request: PatientCreate, doctor_id: int ) -> PatientResponse:
    patient = self.repository.create(db=db, request=request, doctor_id=doctor_id)
    return PatientResponse.model_validate(patient)

  def get_all_patients(self,db: Session,doctor_id: int,skip: int = 0,limit: int = 100,) -> list[PatientResponse]:
    if skip < 0:
      raise ValueError("skip cannot be negative")

    if limit < 1 or limit > 100:
      raise ValueError("limit must be between 1 and 100")

    patients = self.repository.all_patients(db=db, doctor_id=doctor_id, skip=skip, limit=limit)

    return [PatientResponse.model_validate(patient) for patient in patients]

  def get_patient(self,db: Session,patient_id: int,doctor_id: int,) -> PatientResponse:
    print(f"{patient_id} {doctor_id}")
    patient = self.repository.get_by_id(db=db,patient_id=patient_id,doctor_id=doctor_id)

    if patient is None:
      raise PatientNotFoundError(patient_id)

    return PatientResponse.model_validate(patient)

  def update_patient(self,db: Session,patient_id: int,doctor_id: int,request: PatientCreate) -> PatientResponse:
    patient = self.repository.get_by_id(db=db,patient_id=patient_id, doctor_id=doctor_id,)

    if patient is None:
      raise PatientNotFoundError(patient_id)

    updated_patient = self.repository.update(db=db, patient=patient, request=request,
    )

    return PatientResponse.model_validate(updated_patient)

  def delete_patient(self,db: Session,patient_id: int,doctor_id: int) -> None:
    patient = self.repository.get_by_id(db=db,patient_id=patient_id,doctor_id=doctor_id)
    if patient is None:
      raise PatientNotFoundError(patient_id)
    self.repository.delete(db=db, patient=patient)

  def get_patient_count(self,db: Session,doctor_id: int,) -> int:
    return self.repository.count_by_doctor_id(db=db, doctor_id=doctor_id)

