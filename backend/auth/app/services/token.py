import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.tokens import create_access_token
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository


class InvalidRefreshTokenError(Exception):
    pass


def _hash(token: str) -> str:
    # SHA-256 is enough here (unlike passwords): the token is 384 random bits,
    # so there is nothing to brute-force and no need for a slow hash.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TokenService:
    @staticmethod
    def _issue_refresh(db: Session, user_id: int, family_id: str) -> str:
        raw = secrets.token_urlsafe(48)  # the value the client keeps
        expires_at = _now() + timedelta(days=get_settings().refresh_token_expire_days)
        RefreshTokenRepository.add(db, user_id, _hash(raw), family_id, expires_at)
        return raw  # shown once; only its hash is stored

    @staticmethod
    def start_session(db: Session, user: User) -> tuple[str, str]:
        """Login: a brand-new family, so a brand-new session."""
        refresh = TokenService._issue_refresh(db, user.id, str(uuid.uuid4()))
        db.commit()
        return create_access_token(user.id, user.role), refresh

    @staticmethod
    def rotate(db: Session, raw_token: str) -> tuple[str, str]:
        """Trade a refresh token for a new access + refresh pair. Single use."""
        token_hash = _hash(raw_token)
        row = RefreshTokenRepository.get_by_hash(db, token_hash)
        if row is None:
            raise InvalidRefreshTokenError()

        now = _now()

        # Already used or revoked, and someone is presenting it again. Either
        # the client is buggy or the token was stolen. Kill the whole session.
        if row.revoked_at is not None:
            TokenService._burn_family(db, row.family_id)
            raise InvalidRefreshTokenError()

        if RefreshTokenRepository.revoke_if_active(db, token_hash, now) == 0:
            # Lost a race, or it is expired. Re-read to tell which.
            db.refresh(row)
            if row.revoked_at is not None:
                TokenService._burn_family(db, row.family_id)
            else:
                db.rollback()
            raise InvalidRefreshTokenError()

        user = db.scalars(select(User).where(User.id == row.user_id)).first()
        if user is None or not user.is_active:
            # Deactivated accounts cannot keep refreshing.
            TokenService._burn_family(db, row.family_id)
            raise InvalidRefreshTokenError()

        new_refresh = TokenService._issue_refresh(db, user.id, row.family_id)
        db.commit()  # old token revoked + new token stored, together
        return create_access_token(user.id, user.role), new_refresh

    @staticmethod
    def logout(db: Session, raw_token: str) -> None:
        """Revoke the whole session. Never reveals whether the token was valid."""
        row = RefreshTokenRepository.get_by_hash(db, _hash(raw_token))
        if row is not None:
            RefreshTokenRepository.revoke_family(db, row.family_id, _now())
            db.commit()

    @staticmethod
    def _burn_family(db: Session, family_id: str) -> None:
        RefreshTokenRepository.revoke_family(db, family_id, _now())
        db.commit()  # commit now: this must persist even though we then raise
