from sqlalchemy.orm import Session
from app.models.doctor import Doctor

class DoctorRepository:
  @staticmethod
  def get_by_email(db: Session, email: str):
    return(
      db.query(Doctor).filter(Doctor.email == email).first()
    )

  @staticmethod
  def get_by_username(db: Session, username: str):
    return(
      db.query(Doctor).filter(Doctor.username == username).first()
    )

  @staticmethod
  def get_by_id(db: Session, id: int):
    return(db.query(Doctor).filter(Doctor.id == id).first())

  @staticmethod
  def create(db: Session, doctor_data: dict):
    doctor = Doctor(**doctor_data)

    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    return doctor
