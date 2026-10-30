
from sqlalchemy.orm import Session

from app.models.patients import Patient
from app.schemas.patients import PatientCreate


class PatientRepository:
  def create(self,db: Session, request: PatientCreate, doctor_id: int ) -> Patient:
    new_patient = Patient(**request.model_dump(), doctor_id=doctor_id)

    try:
      db.add(new_patient)
      db.commit()
      db.refresh(new_patient)
      return new_patient
    except Exception:
      db.rollback()
      raise

  def get_by_id(self, db: Session, patient_id: int, doctor_id: int) -> Patient | None:
    return (db.query(Patient).filter(Patient.id == patient_id, Patient.doctor_id == doctor_id).first())

  def all_patients(self, db: Session, doctor_id: int, skip: int = 0, limit: int = 100) -> list[Patient]:
    if skip < 0:
      raise ValueError("skip cannot be negative")

    if limit < 1 or limit > 100:
      raise ValueError("limit must be between 1 and 100")

    return (db.query(Patient).filter(Patient.doctor_id == doctor_id).order_by(Patient.id).offset(skip).limit(limit).all())

  def count_by_doctor_id(self, db: Session, doctor_id: int) -> int:
    return (db.query(Patient).filter(Patient.doctor_id == doctor_id).count())

  def update(self,db: Session, patient: Patient, request: PatientCreate) -> Patient:
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
