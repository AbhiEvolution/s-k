from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class NotificationLog(Base):
    """One row per event handled. Doubles as the idempotency record.

    The UNIQUE event_id is what stops a redelivered event from sending a
    second email: the database, not our memory, decides "have I seen this?".
    """

    __tablename__ = "notification_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), unique=True)
    event_type: Mapped[str] = mapped_column(String(50))
    recipient: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30))  # sent | skipped_no_recipient
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
