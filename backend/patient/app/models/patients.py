from sqlalchemy import Column, Integer, String, DateTime, func

from db.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    # The clinic that owns this record (clinic service id; no foreign key).
    # Access = "caller is a member of this clinic", checked via the clinic service.
    clinic_id = Column(Integer, nullable=False, index=True)

    # Audit only: the auth user id of whoever created the record. It grants no access.
    created_by_user_id = Column(Integer, nullable=False, index=True)

    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    address = Column(String(255), nullable=True)
    mobile_number = Column(String(15), nullable=True)
    gender = Column(String(20), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
