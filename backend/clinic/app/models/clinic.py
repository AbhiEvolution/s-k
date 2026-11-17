from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(15))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ClinicMember(Base):
    """Which user belongs to which clinic, and with what role *in that clinic*."""

    __tablename__ = "clinic_members"
    # A user can be a member of a clinic only once.
    __table_args__ = (UniqueConstraint("clinic_id", "user_id", name="uq_clinic_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    # Real foreign key: both tables are in THIS service's database.
    clinic_id: Mapped[int] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), index=True
    )
    # Just a number: the users table lives in the auth service's database, so
    # there is deliberately no foreign key here.
    user_id: Mapped[int] = mapped_column(Integer, index=True)

    role: Mapped[str] = mapped_column(String(20))  # clinic_admin | doctor | staff
