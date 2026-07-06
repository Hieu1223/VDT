from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)
    email: Optional[str] = None
    role: str = Field(description="employee or technician_human")


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserPublic(BaseModel):
    id: str
    username: str
    full_name: str
    email: Optional[str] = None
    role: str
    status: str
    online: bool = False
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserPublic
