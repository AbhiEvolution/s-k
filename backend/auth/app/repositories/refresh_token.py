from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    @staticmethod
    def add(
        db: Session, user_id: int, token_hash: str, family_id: str, expires_at: datetime
    ) -> RefreshToken:
        row = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )
        db.add(row)
        db.flush()
        return row

    @staticmethod
    def get_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return db.scalars(stmt).first()

    @staticmethod
    def revoke_if_active(db: Session, token_hash: str, now: datetime) -> int:
        """Atomically mark a token used. Returns 1 if THIS call won, else 0.

        One UPDATE with the checks in its WHERE clause. If two requests present
        the same token at the same moment, the database lets exactly one of
        them update the row; the other sees 0 rows changed. A read-then-write
        in Python could let both succeed.
        """
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
            .values(revoked_at=now)
        )
        # synchronize_session=False: skip SQLAlchemy's attempt to mirror the change
        # onto in-memory objects (it compares datetimes in Python). Callers that
        # need fresh state use db.refresh().
        return db.execute(stmt, execution_options={"synchronize_session": False}).rowcount

    @staticmethod
    def revoke_family(db: Session, family_id: str, now: datetime) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.execute(stmt, execution_options={"synchronize_session": False})
