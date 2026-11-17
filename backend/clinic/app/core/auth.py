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
    id: int
    role: str  # the account role from the auth service: admin | doctor | patient


@lru_cache
def _jwks_client() -> PyJWKClient:
    # Downloads the public keys and caches them; re-fetches when a token
    # carries an unknown `kid` (that is how key rotation is picked up).
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
    """Who is calling? Verifies the bearer token locally, with no call per request."""
    if credentials is None:
        raise _unauthorized("Missing authentication credentials")

    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            get_signing_key(credentials.credentials),
            algorithms=[ALGORITHM],  # never trust the algorithm named in the token
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except PyJWKClientConnectionError:
        # Not the caller's fault: we could not reach the auth service for keys.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Auth service unavailable")
    except jwt.PyJWTError:
        raise _unauthorized("Could not validate credentials")

    subject = payload["sub"]
    if payload.get("type") != "access" or not str(subject).isdigit() or int(subject) <= 0:
        raise _unauthorized("Could not validate credentials")

    return CurrentUser(id=int(subject), role=str(payload.get("role", "")))
