from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user, get_raw_token
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.services.appointment import AppointmentService
from db.database import get_db

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    data: AppointmentCreate,
    response: Response,
    idempotency_key: str | None = Header(default=None, max_length=64),
    user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_raw_token),
    db: Session = Depends(get_db),
):
    """Book a slot. Send an `Idempotency-Key` header so a retried request
    (network blip, double click) returns the same appointment instead of an error."""
    appointment, created = AppointmentService.book(db, user, token, data, idempotency_key)
    if not created:
        response.status_code = status.HTTP_200_OK  # replay of an earlier request
    return appointment


@router.get("", response_model=list[AppointmentResponse])
def list_appointments(
    clinic_id: int = Query(gt=0),
    doctor_id: int | None = Query(default=None, gt=0),
    patient_id: int | None = Query(default=None, gt=0),
    start_from: datetime | None = Query(default=None, description="inclusive, ISO 8601"),
    start_to: datetime | None = Query(default=None, description="exclusive, ISO 8601"),
    status_filter: Literal["booked", "cancelled"] | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_raw_token),
    db: Session = Depends(get_db),
):
    return AppointmentService.list(
        db, user, token, clinic_id, doctor_id, patient_id, start_from, start_to,
        status_filter, skip, limit,
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_raw_token),
    db: Session = Depends(get_db),
):
    return AppointmentService.get(db, user, token, appointment_id)


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_raw_token),
    db: Session = Depends(get_db),
):
    """Frees the slot. Cancelling an already-cancelled appointment is a no-op."""
    return AppointmentService.cancel(db, user, token, appointment_id)
