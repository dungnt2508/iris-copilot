from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8)
    password_confirm: str = Field(min_length=8)
    phone: Optional[str] = None
    department: Optional[str] = None


class RegisterResponse(BaseModel):
    user_id: str
    email: EmailStr
    username: str
    full_name: str
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class MeResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    full_name: str
    role: str
    permissions: list[str]
    status: str


