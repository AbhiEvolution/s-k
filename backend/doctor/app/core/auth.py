
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from dotenv import load_dotenv
from jose import JWTError, jwt
from fastapi.security import HTTPBearer
# from fastapi.security import OAuth2PasswordBearer

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
  os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
  raise RuntimeError(
    "JWT_SECRET_KEY must be set to at least 32 characters"
  )

# oauth2_scheme = OAuth2PasswordBearer(
#   tokenUrl="/api/v1/auth/login"
# )

oauth2_scheme = HTTPBearer()

class Jwt:

  @staticmethod
  def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
  ) -> str:
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    expire = now + (expires_delta
      if expires_delta is not None
      else timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
      )
    )

    to_encode.update({
      "iat": now,
      "exp": expire,
    })

    return jwt.encode(
      to_encode,
      JWT_SECRET_KEY,
      algorithm=JWT_ALGORITHM,
    )

  @staticmethod
  def get_doctor_id(token: str) -> int:
    payload = jwt.decode(
      token,
      JWT_SECRET_KEY,
      algorithms=[JWT_ALGORITHM],
    )

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.isdigit():
      raise JWTError("Token subject is missing or invalid")

    doctor_id = int(subject)

    if doctor_id <= 0:
      raise JWTError("Token subject is invalid")

    return doctor_id

  @staticmethod
  def create_password_reset_token(doctor_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(doctor_id), "purpose": "password_reset", "iat": now, "exp": now + timedelta(minutes=15),}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

  @staticmethod
  def verify_password_reset_token(token: str) -> int:
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

    if payload.get("purpose") != "password_reset":
      raise JWTError("Invalid token purpose")

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.isdigit():
      raise JWTError("Invalid token subject")

    doctor_id = int(subject)

    if doctor_id <= 0:
      raise JWTError("Invalid doctor ID")

    return doctor_id
