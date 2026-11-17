from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Doctor(Base):
    """A doctor's PROFILE. Identity (email, password) lives in the auth service."""

    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)

    # The auth service's user id. Not a foreign key: it is another database.
    # unique=True: one profile per account, enforced by the database.
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    # The clinic this doctor works at (clinic service id; again no foreign key).
    # Never trusted from the client alone: the service verifies membership by
    # asking the clinic service before saving it.
    clinic_id: Mapped[int | None] = mapped_column(Integer, index=True)

    full_name: Mapped[str] = mapped_column(String(100))
    specialty: Mapped[str | None] = mapped_column(String(100))

    age: Mapped[int | None] = mapped_column(Integer)
    address: Mapped[str | None] = mapped_column(String(255))
    mobile_number: Mapped[str | None] = mapped_column(String(15))
    gender: Mapped[str | None] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
