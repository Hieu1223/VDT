from typing import Optional
from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


class AdminCreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    full_name: str
    email: Optional[str] = None
    role: str


class UpdateUserStatusRequest(BaseModel):
    status: str = Field(description="active, suspended, or deactivated")
