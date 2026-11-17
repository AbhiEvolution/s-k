from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError

from app.core.config import get_settings

ALGORITHM = "RS256"
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: int  # the auth service's user id (the token's `sub`)
    role: str  # admin | doctor | patient


@lru_cache
def _jwks_client() -> PyJWKClient:
    return PyJWKClient(get_settings().auth_jwks_url, cache_keys=True)


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
    """Verify the bearer token locally using the auth service's public key."""
    if credentials is None:
        raise _unauthorized("Missing authentication credentials")

    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            get_signing_key(credentials.credentials),
            algorithms=[ALGORITHM],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
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


def require_role(*roles: str):
    """Dependency factory: the account role must be one of `roles`."""

    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return dependency
