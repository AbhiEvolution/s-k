from datetime import datetime, time

from sqlalchemy import (
    JSON,
    DateTime,
    Index,
    Integer,
    SmallInteger,
    String,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base

BOOKED = "booked"
CANCELLED = "cancelled"

# The WHERE clause of the partial unique indexes below.
_ONLY_BOOKED = text("status = 'booked'")


class Appointment(Base):
    """One booked time. Only ids of other services' data are stored."""

    __tablename__ = "appointments"
    __table_args__ = (
        # THE double-booking guarantee. The database, not Python, refuses a
        # second *booked* appointment for the same doctor at the same time.
        # Cancelled rows are excluded, so a cancelled slot can be booked again.
        Index(
            "uq_booked_doctor_slot", "doctor_id", "starts_at", unique=True,
            postgresql_where=_ONLY_BOOKED, sqlite_where=_ONLY_BOOKED,
        ),
        # A patient cannot be in two places at once either.
        Index(
            "uq_booked_patient_slot", "patient_id", "starts_at", unique=True,
            postgresql_where=_ONLY_BOOKED, sqlite_where=_ONLY_BOOKED,
        ),
        # Same key from the same user = same request retried (idempotency).
        UniqueConstraint("created_by_user_id", "idempotency_key", name="uq_idempotency"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    clinic_id: Mapped[int] = mapped_column(Integer, index=True)
    doctor_id: Mapped[int] = mapped_column(Integer, index=True)
    patient_id: Mapped[int] = mapped_column(Integer, index=True)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Snapshot taken at booking time, so events and later notices need no calls to
    # other services (even if they are down). A deliberate, small copy of data.
    patient_name: Mapped[str | None] = mapped_column(String(100))
    patient_email: Mapped[str | None] = mapped_column(String(255))
    doctor_name: Mapped[str | None] = mapped_column(String(100))

    status: Mapped[str] = mapped_column(String(20), default=BOOKED)
    reason: Mapped[str | None] = mapped_column(String(255))

    created_by_user_id: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str | None] = mapped_column(String(64))

    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_by_user_id: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Availability(Base):
    """A weekly working window for a doctor, e.g. Monday 09:00-12:00 (UTC)."""

    __tablename__ = "availability"
    __table_args__ = (
        UniqueConstraint("doctor_id", "weekday", "start_time", name="uq_doctor_window"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(Integer, index=True)
    clinic_id: Mapped[int] = mapped_column(Integer)

    weekday: Mapped[int] = mapped_column(SmallInteger)  # Monday=0 ... Sunday=6
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)


class OutboxEvent(Base):
    """The transactional outbox.

    An event row is written in the SAME transaction as the change it describes,
    so "appointment saved" and "event recorded" can never disagree. A separate
    relay process publishes unpublished rows to RabbitMQ.
    """

    __tablename__ = "outbox_events"
    __table_args__ = (
        # The relay only ever looks at unpublished rows; keep that lookup tiny.
        Index(
            "ix_outbox_unpublished", "id",
            postgresql_where=text("published_at IS NULL"),
            sqlite_where=text("published_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), unique=True)
    event_type: Mapped[str] = mapped_column(String(50))  # also the routing key
    payload: Mapped[dict] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
