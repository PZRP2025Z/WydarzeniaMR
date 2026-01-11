"""
participation_models.py
=======================

Database models for participation-survey related activities.

Provides SQLModel and Pydantic models for tracking user participation
statuses in events, including going/maybe/not going options.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class ParticipationStatus(str, Enum):
    """
    Enum representing possible participation statuses for an event.

    Options:
    - going: user will attend the event
    - maybe: user may attend
    - not_going: user will not attend
    - invited: user has been invited
    """

    going = "going"
    not_going = "not_going"
    maybe = "maybe"
    invited = "invited"


class ParticipationCreate(BaseModel):
    """
    Pydantic model for creating a participation record.

    :param status: Participation status (going / maybe / not_going)
    """

    status: ParticipationStatus


class EventParticipation(SQLModel, table=True):
    """
    Database table model representing a user's participation in an event.

    :param id: Primary key of the participation record.
    :param user_id: ID of the user participating.
    :param event_id: ID of the event.
    :param status: Participation status (going / maybe / not_going / invited).
    :param created_at: Timestamp when participation was created.
    :param updated_at: Timestamp when participation was last updated.
    """

    __tablename__ = "event_participations"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    status: ParticipationStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
