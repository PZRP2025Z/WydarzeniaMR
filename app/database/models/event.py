"""
Event database model
"""

from sqlmodel import SQLModel, Field
from datetime import datetime


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: int = Field(default=None, primary_key=True)
    name: str
    location: str
    photo: bytes | None = (
        None  # Photo is stored as bytes. We don't have any cloud storage to use URLs, so for the project's sake we save it directly in the database.
    )
    time: datetime
    description: str | None = None
    owner_id: int = Field(foreign_key="users.id")


class EventCreate(SQLModel):
    name: str
    location: str
    photo: bytes | None = None
    time: datetime
    description: str | None = None


class EventUpdate(SQLModel):
    name: str | None = None
    location: str | None = None
    photo: bytes | None = None
    time: datetime | None = None
    description: str | None = None
