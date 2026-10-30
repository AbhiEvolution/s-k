from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.doctor import DoctorRepository
from app.core.security import PasswordSecurity
from app.core.auth import Jwt
from jose import JWTError

class AuthService:
  @staticmethod
  def prepare_password_reset(db: Session, email: str) -> tuple[str, str] | None:
    doctor = DoctorRepository.get_by_email(db, email)
    if doctor is None:
      return None

    token = Jwt.create_password_reset_token(doctor.id)
    return doctor.email, token

  @staticmethod
  def login(db: Session, email: str, password: str):
    
    doctor = DoctorRepository.get_by_email(db, email)
    if doctor is None:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
      )
    
    is_vaild = PasswordSecurity.verify_password(password, doctor.password)
    if not is_vaild:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
      )

    access_token = Jwt.create_access_token(data={"sub": str(doctor.id)})
    return {"access_token": access_token, "token_type": "bearer"}

  @staticmethod
  def reset_password(db: Session, token: str, new_password: str) -> dict[str, str]:
    try:
      doctor_id = Jwt.verify_password_reset_token(token)
    except JWTError:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired reset token",
      )

    doctor = DoctorRepository.get_by_id(db, doctor_id)
    if doctor is None:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired reset token",
      )

    doctor.password = PasswordSecurity.hash_password(new_password)
    db.commit()
    return {"message": "Password reset successfully"}
