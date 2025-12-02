"""
Models for user logging, registration and authorization
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class RegisterUserRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None

    def get_uuid(self) -> Optional[UUID]:
        if self.user_id:
            return UUID(int=self.user_id)
        return None
