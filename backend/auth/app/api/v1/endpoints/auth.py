from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.token import RefreshRequest, TokenResponse
from app.schemas.user import LoginRequest, RegisterRequest, UserResponse
from app.services.auth import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.services.token import InvalidRefreshTokenError, TokenService
from db.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(access: str, refresh: str) -> TokenResponse:
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=get_settings().access_token_expire_minutes * 60,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        return AuthService.register(db, data.email, data.password, data.role)
    except EmailAlreadyRegisteredError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = AuthService.login(db, data.email, data.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _token_response(*TokenService.start_session(db, user))


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    try:
        return _token_response(*TokenService.rotate(db, data.refresh_token))
    except InvalidRefreshTokenError:
        # One message for unknown, expired, reused and revoked tokens.
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: RefreshRequest, db: Session = Depends(get_db)):
    # Always 204: logout is idempotent and must not reveal if a token was valid.
    TokenService.logout(db, data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
