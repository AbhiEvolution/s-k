from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import MAX_PASSWORD_BYTES


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    # Public sign-up may only create these roles. Admin accounts are never
    # self-registered.
    role: Literal["admin", "doctor", "patient"]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError("Password must be at most 72 bytes")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    # Never include password_hash here.
    id: int
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)
