from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ClinicRole = Literal["clinic_admin", "doctor", "staff"]


class ClinicCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, pattern=r"^\+?\d{10,15}$")


class ClinicResponse(BaseModel):
    id: int
    name: str
    address: str | None
    phone: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberCreate(BaseModel):
    user_id: int = Field(gt=0)
    role: ClinicRole


class MemberResponse(BaseModel):
    user_id: int
    role: str

    model_config = ConfigDict(from_attributes=True)
