from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.auth import Jwt, oauth2_scheme
from app.models.doctor import Doctor
from db.database import get_db

def get_current_doctor(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Doctor:
  try:
    doctor_id = Jwt.get_doctor_id(credentials.credentials)
  except JWTError:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid or expired token",
      headers={"WWW-Authenticate": "Bearer"}
    )
  doctor = db.query(Doctor).filter(Doctor.id==doctor_id).first()

  if doctor is None:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Doctor not found",
      headers={"WWW-Authenticate":"Bearer"}
    )

  return doctor
