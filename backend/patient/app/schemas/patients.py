from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class PatientUpdate(BaseModel):
  """Editable fields. A patient cannot be moved to another clinic via PUT."""

  name: str = Field(min_length=3, max_length=100)
  age: int = Field(gt=0, lt=130)
  address: str = Field(min_length=3, max_length=255)
  mobile_number: str = Field(pattern=r"^\+?\d{10,15}$")
  gender: Literal["female", "male", "other", "prefer_not_to_say"]
  email: EmailStr | None = None


class PatientCreate(PatientUpdate):
  clinic_id: int = Field(gt=0)


class PatientResponse(BaseModel):
  id: int
  clinic_id: int
  created_by_user_id: int
  name: str
  age: int
  address: str
  mobile_number: str
  gender: str
  email: EmailStr | None = None
  created_at: datetime
  updated_at: datetime

  model_config = ConfigDict(from_attributes=True)
