"""
auth_models.py
===============

Database models for authentication-related activities.

Provides Pydantic models for user registration, login, and JWT token handling.
"""

from uuid import UUID
from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    """
    Model for registering a new user.

    :param login: Login/username of the new user.
    :param email: Email address of the new user.
    :param password: Plain-text password of the new user.
    """

    login: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """
    Model for logging in an existing user.

    :param email: Email address of the user.
    :param password: Plain-text password of the user.
    """

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Model representing JWT access token response.

    :param access_token: JWT access token string.
    :param token_type: Type of the token (usually 'bearer').
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Model representing decoded JWT token data.

    :param user_id: ID of the user associated with the token (optional).
    """

    user_id: int | None = None

    def get_uuid(self) -> UUID | None:
        """
        Convert user_id to UUID if present.

        :return: UUID object if user_id is set, None otherwise.
        """
        if self.user_id is not None:
            return UUID(int=self.user_id)
        return None
