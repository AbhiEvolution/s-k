from sqlalchemy import Column, Integer, String, DateTime, func

from db.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    # ID of the doctor who owns this patient
    doctor_id = Column(Integer, nullable=False, index=True)

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