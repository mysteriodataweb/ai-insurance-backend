from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import UTCDateTime

UserRole = Literal["adjuster", "underwriter", "manager"]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = "adjuster"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    created_at: UTCDateTime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
