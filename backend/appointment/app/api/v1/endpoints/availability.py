from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user, get_raw_token, require_role
from app.schemas.appointment import (
    AvailabilityResponse,
    AvailabilityUpdate,
    SlotResponse,
)
from app.services.appointment import AvailabilityService
from db.database import get_db

router = APIRouter(prefix="/appointments", tags=["availability"])


@router.put("/availability", response_model=AvailabilityResponse)
def replace_my_availability(
    data: AvailabilityUpdate,
    _user: CurrentUser = Depends(require_role("doctor")),
    token: str = Depends(get_raw_token),
    db: Session = Depends(get_db),
):
    """A doctor replaces their own weekly working hours (UTC)."""
    return AvailabilityService.replace_my_availability(db, token, data)


@router.get("/availability", response_model=AvailabilityResponse)
def get_availability(
    doctor_id: int = Query(gt=0),
    user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_raw_token),
    db: Session = Depends(get_db),
):
    return AvailabilityService.get_availability(db, user, token, doctor_id)


@router.get("/slots", response_model=list[SlotResponse])
def get_slots(
    doctor_id: int = Query(gt=0),
    day: date = Query(description="YYYY-MM-DD (UTC)"),
    user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_raw_token),
    db: Session = Depends(get_db),
):
    """Every slot the doctor offers that day, each marked available or not."""
    return AvailabilityService.get_slots(db, user, token, doctor_id, day)
