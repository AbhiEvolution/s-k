import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.tokens import verify_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """Only platform admins (account role "admin") may call the endpoint."""
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        claims = verify_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise unauthorized
    if claims.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admins only")
    return claims
