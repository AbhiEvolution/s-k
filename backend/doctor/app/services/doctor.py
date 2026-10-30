from sqlalchemy.orm import Session

from app.repositories.doctor import DoctorRepository
from app.core.security import PasswordSecurity

class DoctorService:
  @staticmethod 
  def create_doctor(db: Session, data):
    if DoctorRepository.get_by_email(db, data.email):
      raise ValueError("Email already registered")
    if DoctorRepository.get_by_username(db, data.username):
      raise ValueError("Username already registered")

    doctor_data = data.model_dump(exclude={"password"})
    doctor_data["password"] = PasswordSecurity.hash_password(data.password)

    return DoctorRepository.create(db, doctor_data)
