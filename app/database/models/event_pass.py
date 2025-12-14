"""
Models for event passes
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone


class EventPass(SQLModel, table=True):
    __tablename__ = "event_passes"

    id: Optional[int] = Field(default=None, primary_key=True)

    token_hash: str = Field(index=True, unique=True)
    event_id: int = Field(index=True)

    user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    display_name: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
