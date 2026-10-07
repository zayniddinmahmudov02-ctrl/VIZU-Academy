from pydantic import BaseModel, EmailStr, Field

from app.schemas.auth.user import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class EmailRequest(BaseModel):
    email: EmailStr


class EmailCodeRequest(BaseModel):
    """6-digit code + the address it was sent to. Format is validated, but a
    malformed code still counts as a failed attempt in the service."""

    email: EmailStr
    code: str = Field(min_length=1, max_length=12)


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=1, max_length=12)
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class MessageResponse(BaseModel):
    message: str


class VerifyCodeResponse(BaseModel):
    valid: bool


class VerifyAdminPasswordRequest(BaseModel):
    password: str
