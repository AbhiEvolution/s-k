from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.permissions import require_clinic_role
from app.models.clinic import ClinicMember
from app.repositories.clinic import MemberRepository
from app.schemas.clinic import MemberCreate, MemberResponse
from app.services.clinic import (
    AlreadyMemberError,
    ClinicService,
    LastAdminError,
    MemberNotFoundError,
)
from db.database import get_db

router = APIRouter(prefix="/clinics/{clinic_id}/members", tags=["members"])


@router.get("", response_model=list[MemberResponse])
def list_members(
    clinic_id: int,
    _member: ClinicMember = Depends(require_clinic_role()),
    db: Session = Depends(get_db),
):
    return MemberRepository.list_for_clinic(db, clinic_id)


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    clinic_id: int,
    data: MemberCreate,
    _member: ClinicMember = Depends(require_clinic_role("clinic_admin")),
    db: Session = Depends(get_db),
):
    try:
        return ClinicService.add_member(db, clinic_id, data)
    except AlreadyMemberError:
        raise HTTPException(status.HTTP_409_CONFLICT, "User is already a member")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    clinic_id: int,
    user_id: int,
    _member: ClinicMember = Depends(require_clinic_role("clinic_admin")),
    db: Session = Depends(get_db),
):
    try:
        ClinicService.remove_member(db, clinic_id, user_id)
    except MemberNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    except LastAdminError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cannot remove the last clinic admin")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
