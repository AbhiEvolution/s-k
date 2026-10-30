from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Literal

class DoctorCreate(BaseModel):
  username: str = Field(min_length=3, max_length=100)
  email: EmailStr
  password: str = Field(min_length=8, max_length=72)
  age: int | None = Field(default=None, ge=0, le=130)
  address: str | None = Field(default=None, max_length=225)
  mobile_number: str = Field(pattern=r"^\+?\d{10,15}$")
  gender: Literal["female", "male", "other", "prefer_not_to_say"]

class DoctorResponse(BaseModel):
  id: int
  username: str
  email: EmailStr
  age: int | None = None
  address: str | None = None
  mobile_number: str | None = None
  gender: str | None = None

  model_config = ConfigDict(from_attributes=True)
