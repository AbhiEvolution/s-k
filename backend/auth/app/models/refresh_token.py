from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class RefreshToken(Base):
    """One row per refresh token ever issued. Rows are revoked, not deleted,
    so a replayed old token can be recognised as theft."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # We store only a hash. A database leak then does not leak usable tokens.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # All tokens descended from one login share a family_id (one "session").
    # Rotating keeps the family; reuse detection revokes the whole family.
    family_id: Mapped[str] = mapped_column(String(36), index=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
