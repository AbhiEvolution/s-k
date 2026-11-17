from sqlalchemy.orm import Session

from app.models.patients import Patient
from app.schemas.patients import PatientCreate, PatientUpdate


class PatientRepository:
  def create(self, db: Session, request: PatientCreate, created_by_user_id: int) -> Patient:
    new_patient = Patient(**request.model_dump(), created_by_user_id=created_by_user_id)

    try:
      db.add(new_patient)
      db.commit()
      db.refresh(new_patient)
      return new_patient
    except Exception:
      db.rollback()
      raise

  def get_by_id(self, db: Session, patient_id: int) -> Patient | None:
    # Not scoped here: the SERVICE checks clinic membership using the row's clinic_id.
    return db.query(Patient).filter(Patient.id == patient_id).first()

  def all_patients(self, db: Session, clinic_id: int, skip: int = 0, limit: int = 100) -> list[Patient]:
    return (
      db.query(Patient).filter(Patient.clinic_id == clinic_id)
      .order_by(Patient.id).offset(skip).limit(limit).all()
    )

  def count_by_clinic_id(self, db: Session, clinic_id: int) -> int:
    return db.query(Patient).filter(Patient.clinic_id == clinic_id).count()

  def update(self, db: Session, patient: Patient, request: PatientUpdate) -> Patient:
    for field, value in request.model_dump().items():
      setattr(patient, field, value)

    try:
      db.commit()
      db.refresh(patient)
      return patient
    except Exception:
      db.rollback()
      raise

  def delete(self, db: Session, patient: Patient) -> None:
    try:
      db.delete(patient)
      db.commit()
    except Exception:
      db.rollback()
      raise
