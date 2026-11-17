from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class User(Base):
    """Identity only. Profile data (specialty, age...) lives in other services."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # unique=True creates a unique index: the database itself prevents
    # duplicate emails, even if two requests arrive at the same moment.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    role: Mapped[str] = mapped_column(String(20))  # doctor | patient | ...
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
