"""
User database model
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    login: str

    email: Optional[str] = Field(index=True, unique=True)
    hashed_password: Optional[str]

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_guest: bool = Field(default=False)


class UserResponse(BaseModel):
    id: int
    login: str
    email: EmailStr


class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
    new_password_confirm: str = Field(..., min_length=6)
