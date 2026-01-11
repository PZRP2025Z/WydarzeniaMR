"""
@file user_models.py
@brief Database models for User-related activities.

Provides SQLModel and Pydantic models for users, including guest users,
password management, and API response structures.
"""

from datetime import datetime, timezone
from typing import NamedTuple

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    @brief Database table model representing a user.

    @param id Primary key of the user.
    @param login User login or display name.
    @param email Optional email address (unique, indexed).
    @param hashed_password Optional hashed password for authentication.
    @param created_at Timestamp of user creation (UTC).
    @param is_guest Boolean indicating whether the user is a guest.
    """

    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    login: str
    email: str | None = Field(index=True, unique=True)
    hashed_password: str | None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_guest: bool = Field(default=False)


class UserResponse(BaseModel):
    """
    @brief Pydantic model representing a user in API responses.

    @param id User ID.
    @param login User login.
    @param email User email address.
    """

    id: int
    login: str
    email: EmailStr


class PasswordChange(BaseModel):
    """
    @brief Pydantic model for changing a user's password.

    @param current_password Current password of the user.
    @param new_password New password to set.
    @param new_password_confirm Confirmation of the new password.
    """

    current_password: str
    new_password: str
    new_password_confirm: str


class UserEmailInfo(NamedTuple):
    """Container for user email information."""

    email: str
    login: str
