from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.core.permissions import require_clinic_role
from app.models.clinic import ClinicMember
from app.repositories.clinic import ClinicRepository
from app.schemas.clinic import ClinicCreate, ClinicResponse
from app.services.clinic import ClinicService
from db.database import get_db

router = APIRouter(prefix="/clinics", tags=["clinics"])


@router.post("", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED)
def create_clinic(
    data: ClinicCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Account-level rule (from auth's role claim): only platform admins
    # create clinics. Clinic-level roles are checked elsewhere.
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins can create clinics")
    return ClinicService.create_clinic(db, user.id, data)


@router.get("", response_model=list[ClinicResponse])
def list_my_clinics(
    user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return ClinicRepository.list_for_user(db, user.id)


@router.get("/{clinic_id}", response_model=ClinicResponse)
def get_clinic(
    clinic_id: int,
    _member: ClinicMember = Depends(require_clinic_role()),  # any member
    db: Session = Depends(get_db),
):
    return ClinicRepository.get(db, clinic_id)


@router.put("/{clinic_id}", response_model=ClinicResponse)
def update_clinic(
    clinic_id: int,
    data: ClinicCreate,
    _member: ClinicMember = Depends(require_clinic_role("clinic_admin")),
    db: Session = Depends(get_db),
):
    clinic = ClinicRepository.get(db, clinic_id)
    return ClinicService.update_clinic(db, clinic, data)
