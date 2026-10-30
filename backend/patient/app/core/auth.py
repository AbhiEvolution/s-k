import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
  raise RuntimeError("JWT_SECRET_KEY must be set to at least 32 characters")

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_doctor_id(
  credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
  if credentials is None:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Missing authentication credentials",
      headers={"WWW-Authenticate": "Bearer"},
    )

  try:
    payload = jwt.decode(
      credentials.credentials,
      JWT_SECRET_KEY,
      algorithms=[JWT_ALGORITHM],
    )

    if payload.get("purpose") == "password_reset":
      raise JWTError("Password reset token cannot access APIs")

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.isdigit():
      raise JWTError("Invalid doctor ID")

    doctor_id = int(subject)

    if doctor_id <= 0:
      raise JWTError("Doctor ID must be positive")

    return doctor_id

  except (JWTError, KeyError, TypeError, ValueError) as exc:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Could not validate credentials",
      headers={"WWW-Authenticate": "Bearer"},
    ) from exc
