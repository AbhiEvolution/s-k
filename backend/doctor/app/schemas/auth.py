from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

class LoginRequest(BaseModel):
  email: EmailStr
  password: str = Field(min_length=1)

class PasswordResetEmailRequest(BaseModel):
  email: EmailStr


class TokenResponse(BaseModel):
  access_token: str
  token_type: str = "bearer"

class ResetPasswordRequest(BaseModel):
  token: str = Field(min_length=1)
  new_password: SecretStr = Field(min_length=8)

  @field_validator("new_password")
  @classmethod
  def validate_password_length(cls, password: SecretStr) -> SecretStr:
    if len(password.get_secret_value().encode("utf-8")) > 72:
      raise ValueError("Password must be at most 72 UTF-8 bytes")
    return password
