import os
from dataclasses import dataclass
from functools import lru_cache

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError

load_dotenv()

# The auth service's PUBLIC keys. There is no shared secret any more.
AUTH_JWKS_URL = os.getenv("AUTH_JWKS_URL", "http://localhost:8003/.well-known/jwks.json")
JWT_ISSUER = os.getenv("JWT_ISSUER", "auth-service")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "clinic-platform")
ALGORITHM = "RS256"

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
  id: int  # the auth service's user id (the token's `sub`)
  role: str  # admin | doctor | patient


@lru_cache
def _jwks_client() -> PyJWKClient:
  return PyJWKClient(AUTH_JWKS_URL, cache_keys=True)


def get_signing_key(token: str):
  """Public key matching the token's `kid`. Tests replace this function."""
  return _jwks_client().get_signing_key_from_jwt(token).key


def _unauthorized(detail: str) -> HTTPException:
  return HTTPException(
    status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
  )


def get_current_user(
  credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
  if credentials is None:
    raise _unauthorized("Missing authentication credentials")

  try:
    payload = jwt.decode(
      credentials.credentials,
      get_signing_key(credentials.credentials),
      algorithms=[ALGORITHM],
      audience=JWT_AUDIENCE,
      issuer=JWT_ISSUER,
      options={"require": ["exp", "iat", "sub", "iss", "aud"]},
    )
  except PyJWKClientConnectionError:
    raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Auth service unavailable")
  except jwt.PyJWTError:
    raise _unauthorized("Could not validate credentials")

  subject = payload["sub"]
  if payload.get("type") != "access" or not str(subject).isdigit() or int(subject) <= 0:
    raise _unauthorized("Could not validate credentials")

  return CurrentUser(id=int(subject), role=str(payload.get("role", "")))


def get_raw_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
  # get_current_user already verified it; we only forward it to the clinic service.
  return credentials.credentials
