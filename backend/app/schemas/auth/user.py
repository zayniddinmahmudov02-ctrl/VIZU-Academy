from pydantic import BaseModel, ConfigDict, EmailStr

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

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str