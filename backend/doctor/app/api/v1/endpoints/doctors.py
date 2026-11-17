from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, bearer_scheme, get_current_user, require_role
from app.core.clinic_client import ClinicServiceUnavailableError, NotClinicMemberError
from app.schemas.doctor import DoctorProfile, DoctorPublic, DoctorResponse
from app.services.doctor import (
    DoctorService,
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)
from db.database import get_db

router = APIRouter(prefix="/doctors", tags=["Doctors"])

NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Doctor profile not found")


def _raw_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    # get_current_user has already verified this token; we only forward it.
    return credentials.credentials


@router.post("", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_my_profile(
    data: DoctorProfile,
    user: CurrentUser = Depends(require_role("doctor")),
    token: str = Depends(_raw_token),
    db: Session = Depends(get_db),
):
    # The owner is the token's user, never a value from the request body.
    try:
        return DoctorService.create_profile(db, user.id, token, data)
    except ProfileAlreadyExistsError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Profile already exists")
    except NotClinicMemberError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not a doctor in that clinic")
    except ClinicServiceUnavailableError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Clinic service unavailable")


@router.get("", response_model=list[DoctorPublic])
def list_clinic_doctors(
    clinic_id: int = Query(gt=0),
    user: CurrentUser = Depends(get_current_user),
    token: str = Depends(_raw_token),
    db: Session = Depends(get_db),
):
    """The doctors of one clinic (public cards). Members of that clinic only."""
    try:
        return DoctorService.list_for_clinic(db, user.id, token, clinic_id)
    except NotClinicMemberError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not a member of that clinic")
    except ClinicServiceUnavailableError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Clinic service unavailable")


# Declared before "/{doctor_id}" so "me" is not parsed as an id.
@router.get("/me", response_model=DoctorResponse)
def get_my_profile(
    user: CurrentUser = Depends(require_role("doctor")), db: Session = Depends(get_db)
):
    try:
        return DoctorService.get_my_profile(db, user.id)
    except ProfileNotFoundError:
        raise NOT_FOUND


@router.put("/me", response_model=DoctorResponse)
def update_my_profile(
    data: DoctorProfile,
    user: CurrentUser = Depends(require_role("doctor")),
    token: str = Depends(_raw_token),
    db: Session = Depends(get_db),
):
    try:
        return DoctorService.update_my_profile(db, user.id, token, data)
    except ProfileNotFoundError:
        raise NOT_FOUND
    except NotClinicMemberError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not a doctor in that clinic")
    except ClinicServiceUnavailableError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Clinic service unavailable")


@router.get("/{doctor_id}", response_model=DoctorPublic)
def get_doctor(
    doctor_id: int,
    _user: CurrentUser = Depends(get_current_user),  # any logged-in user
    db: Session = Depends(get_db),
):
    try:
        return DoctorService.get_public(db, doctor_id)
    except ProfileNotFoundError:
        raise NOT_FOUND
