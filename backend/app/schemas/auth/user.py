from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from uuid import UUID
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


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