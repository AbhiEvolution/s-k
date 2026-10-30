from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from db.database import get_db
from app.core.email import send_password_reset_email
from app.schemas.auth import (
  LoginRequest,
  PasswordResetEmailRequest,
  ResetPasswordRequest,
  TokenResponse,
)
from app.services.auth import AuthService

router = APIRouter(
  prefix="/doctors",
  tags=["Doctors"], 
)

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db),):
  return AuthService.login(db=db, email=data.email, password=data.password)

@router.post(
  "/request-password-reset",
  status_code=status.HTTP_202_ACCEPTED,
)
def request_password_reset(
  data: PasswordResetEmailRequest,
  background_tasks: BackgroundTasks,
  db: Session = Depends(get_db),
):
  reset_details = AuthService.prepare_password_reset(db, data.email)
  if reset_details is not None:
    email, token = reset_details
    background_tasks.add_task(send_password_reset_email, email, token)

  return {
    "message": "If an account exists for this email, a password reset link will be sent."
  }

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
  return AuthService.reset_password(db=db, token=data.token, new_password=data.new_password.get_secret_value())