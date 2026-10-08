from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from uuid import UUID
# Same password rule as the existing frontend forms and ChangePasswordRequest
# (min 6) — plus an upper bound so a huge body can't reach the hash function.
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 128


class UserRegister(BaseModel):
    """Self-registration: name, ONE login identifier (e-mail or phone
    number — see services/auth/identifier.py), password twice. `email` is
    accepted as a legacy alias of `identifier`. No confirmation step."""

    identifier: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    password_confirm: str | None = Field(default=None, max_length=PASSWORD_MAX_LENGTH)
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    # older clients may still send a username instead of a name
    username: str | None = Field(default=None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")

    @model_validator(mode="after")
    def _check(self):
        if not (self.login_identifier or "").strip():
            raise ValueError("identifier is required.")
        if not (self.full_name and self.full_name.strip()) and not self.username:
            raise ValueError("full_name is required.")
        if not self.password.strip():
            raise ValueError("Password must not be empty.")
        if self.password_confirm is not None and self.password_confirm != self.password:
            raise ValueError("PASSWORD_MISMATCH")
        return self

    @property
    def login_identifier(self) -> str:
        return (self.identifier or self.email or "").strip()


class UserLogin(BaseModel):
    """`identifier` = e-mail or phone number; `email` is the legacy alias
    (admin / teacher / older clients keep working unchanged)."""

    identifier: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(max_length=PASSWORD_MAX_LENGTH)

    @model_validator(mode="after")
    def _check(self):
        if not (self.login_identifier or "").strip():
            raise ValueError("identifier is required.")
        return self

    @property
    def login_identifier(self) -> str:
        return (self.identifier or self.email or "").strip()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    # Plain str on OUTPUT: Telegram / phone accounts carry internal
    # placeholder addresses (e.g. @telegram.local) that EmailStr rejects,
    # which made GET /users/me fail for them.
    email: str
    username: str
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    # set for accounts that log in with a phone number
    login_phone: str | None = None
    country: str | None = None
    profile_image: str | None = None
    preferred_language: str
    is_active: bool
    is_verified: bool
    is_banned: bool
    suspended_until: datetime | None = None
    role: str
    created_at: datetime

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