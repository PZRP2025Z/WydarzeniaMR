from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel


class ParticipationStatus(str, Enum):
    going = "going"
    not_going = "not_going"
    maybe = "maybe"


class ParticipationCreate(BaseModel):
    status: ParticipationStatus


class EventParticipation(SQLModel, table=True):
    __tablename__ = "event_participations"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id", index=True)
    event_id: int = Field(foreign_key="events.id", index=True)

    status: ParticipationStatus

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
