from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.models.clinic import ClinicMember
from app.repositories.clinic import MemberRepository
from db.database import get_db


def require_clinic_role(*allowed_roles: str):
    """Build a dependency: 'caller must belong to {clinic_id} with one of these roles'.

    Usage:  member = Depends(require_clinic_role("clinic_admin"))
    With no roles given, any member passes.

    This is the multi-tenancy rule in one place. Every clinic-scoped endpoint
    uses it, so a forgotten check cannot leak another clinic's data.
    """

    def dependency(
        clinic_id: int,  # taken from the URL path
        user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> ClinicMember:
        member = MemberRepository.get(db, clinic_id, user.id)

        if member is None:
            # 404, not 403: do not reveal that this clinic exists to outsiders.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Clinic not found")

        if allowed_roles and member.role not in allowed_roles:
            # They are a member, so existence is not secret; say what's missing.
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient clinic role")

        return member

    return dependency
