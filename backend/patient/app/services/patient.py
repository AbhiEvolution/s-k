from sqlalchemy.orm import Session

from app.core.clinic_client import NotClinicMemberError, verify_membership
from app.core.exceptions import PatientNotFoundError
from app.models.patients import Patient
from app.repositories.patients import PatientRepository
from app.schemas.patients import PatientCreate, PatientResponse, PatientUpdate


class PatientService:
  def __init__(self):
    self.repository = PatientRepository()

  def _load_authorized(self, db: Session, patient_id: int, user_id: int, token: str) -> Patient:
    """Fetch a patient only if the caller belongs to its clinic.

    Outsiders get the same "not found" as a missing id, so patient ids in
    other clinics cannot be probed.
    """
    patient = self.repository.get_by_id(db=db, patient_id=patient_id)
    if patient is None:
      raise PatientNotFoundError(patient_id)
    try:
      verify_membership(patient.clinic_id, user_id, token)
    except NotClinicMemberError:
      raise PatientNotFoundError(patient_id)
    return patient

  def create_patient(self, db: Session, request: PatientCreate, user_id: int, token: str) -> PatientResponse:
    verify_membership(request.clinic_id, user_id, token)  # NotClinicMemberError -> 403
    patient = self.repository.create(db=db, request=request, created_by_user_id=user_id)
    return PatientResponse.model_validate(patient)

  def get_all_patients(self, db: Session, clinic_id: int, user_id: int, token: str,
                       skip: int = 0, limit: int = 100) -> list[PatientResponse]:
    verify_membership(clinic_id, user_id, token)
    patients = self.repository.all_patients(db=db, clinic_id=clinic_id, skip=skip, limit=limit)
    return [PatientResponse.model_validate(patient) for patient in patients]

  def get_patient(self, db: Session, patient_id: int, user_id: int, token: str) -> PatientResponse:
    patient = self._load_authorized(db, patient_id, user_id, token)
    return PatientResponse.model_validate(patient)

  def update_patient(self, db: Session, patient_id: int, user_id: int, token: str,
                     request: PatientUpdate) -> PatientResponse:
    patient = self._load_authorized(db, patient_id, user_id, token)
    updated = self.repository.update(db=db, patient=patient, request=request)
    return PatientResponse.model_validate(updated)

  def delete_patient(self, db: Session, patient_id: int, user_id: int, token: str) -> None:
    patient = self._load_authorized(db, patient_id, user_id, token)
    self.repository.delete(db=db, patient=patient)

  def get_patient_count(self, db: Session, clinic_id: int, user_id: int, token: str) -> int:
    verify_membership(clinic_id, user_id, token)
    return self.repository.count_by_clinic_id(db=db, clinic_id=clinic_id)
