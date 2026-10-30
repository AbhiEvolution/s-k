from sqlalchemy import Column, Integer, String, DateTime, func
from db.database import Base


class Doctor(Base):
  __tablename__ = "doctors"

  id = Column(Integer, primary_key=True, index=True)

  username = Column(String(100), unique=True, index=True, nullable=False)
  email = Column(String(100), unique=True, index=True, nullable=False)
  password = Column(String(255), nullable=False)

  age = Column(Integer, nullable=True)
  address = Column(String(255), nullable=True)
  mobile_number = Column(String(15), nullable=True)
  gender = Column(String(20), nullable=True)

  created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)