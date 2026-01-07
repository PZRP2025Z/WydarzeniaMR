"""
@file event_models.py
@brief Database models for event-related activities.

Provides SQLModel and Pydantic models for storing events, creating new events,
and updating existing events.
"""

from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Event(SQLModel, table=True):
    """
    @brief Database table model representing an event.

    @param id Primary key of the event.
    @param name Name of the event.
    @param location Location where the event takes place.
    @param photo Optional photo stored as bytes (no external cloud storage).
    @param time Date and time of the event.
    @param description Optional description of the event.
    @param owner_id ID of the user who owns/created the event.
    """

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


class EventCreate(BaseModel):
    """
    @brief Pydantic model for creating a new event.

    @param name Name of the event.
    @param location Location of the event.
    @param photo Optional photo as bytes.
    @param time Date and time of the event.
    @param description Description of the event.
    """

    name: str
    location: str
    photo: bytes | None = None
    time: datetime
    description: str


class EventUpdate(BaseModel):
    """
    @brief Pydantic model for updating an existing event.

    All fields are optional; only provided fields will be updated.

    @param name Optional updated name of the event.
    @param location Optional updated location.
    @param photo Optional updated photo as bytes.
    @param time Optional updated date and time.
    @param description Optional updated description.
    """

    name: str | None = None
    location: str | None = None
    photo: bytes | None = None
    time: datetime | None = None
    description: str | None = None
