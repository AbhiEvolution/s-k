from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DoctorProfile(BaseModel):
    """Input for create and update. No email or password: that is auth's job."""

    full_name: str = Field(min_length=2, max_length=100)
    clinic_id: int | None = Field(default=None, gt=0)
    specialty: str | None = Field(default=None, max_length=100)
    age: int | None = Field(default=None, ge=18, le=130)
    address: str | None = Field(default=None, max_length=255)
    mobile_number: str | None = Field(default=None, pattern=r"^\+?\d{10,15}$")
    gender: Literal["female", "male", "other", "prefer_not_to_say"] | None = None


class DoctorResponse(DoctorProfile):
    """What the doctor sees about themselves."""

    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class DoctorPublic(BaseModel):
    """What any logged-in user may see. Deliberately omits phone, address, age."""

    id: int
    full_name: str
    specialty: str | None
    clinic_id: int | None

    model_config = ConfigDict(from_attributes=True)
