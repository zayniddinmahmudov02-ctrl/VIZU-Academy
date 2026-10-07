from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from uuid import UUID
# Same password rule as the existing frontend forms and ChangePasswordRequest
# (min 6) — plus an upper bound so a huge body can't reach the hash function.
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 128


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    # "Vor- und Nachname" — the registration form sends this; older clients
    # may still send a username instead. At least one of the two is required.
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    username: str | None = Field(default=None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")

    @model_validator(mode="after")
    def _name_or_username(self):
        if not (self.full_name and self.full_name.strip()) and not self.username:
            raise ValueError("full_name is required.")
        if not self.password.strip():
            raise ValueError("Password must not be empty.")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    country: str | None = None
    profile_image: str | None = None
    preferred_language: str
    is_active: bool
    is_verified: bool
    is_banned: bool
    suspended_until: datetime | None = None
    role: str
    created_at: datetime

class RegisterResponse(UserResponse):
    """Registration result — the account exists but must confirm its email."""

    email_verification_required: bool
    verification_email_sent: bool


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class ProfileUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=30)
    country: str | None = Field(default=None, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class LanguageUpdateRequest(BaseModel):
    language: Literal["de", "uz"]