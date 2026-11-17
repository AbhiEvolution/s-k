from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.repositories.user import UserRepository
from app.schemas.user import UserResponse
from db.database import get_db

router = APIRouter(prefix="/auth/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def lookup_users(
    email: str | None = Query(default=None, max_length=255),
    ids: str | None = Query(default=None, description="comma-separated user ids, at most 100"),
    _admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Find accounts by exact email or by id. Platform admins only.

    Deliberately NOT a search or a listing: you must already know the email or
    the ids, so this cannot be used to browse everyone's accounts.
    """
    if (email is None) == (ids is None):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Provide exactly one of: email, ids")

    if email is not None:
        user = UserRepository.get_by_email(db, email.strip().lower())
        return [user] if user else []

    try:
        wanted = [int(part) for part in ids.split(",") if part.strip()]
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "ids must be integers")
    if not wanted or len(wanted) > 100:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Provide between 1 and 100 ids")
    return UserRepository.get_by_ids(db, wanted)
