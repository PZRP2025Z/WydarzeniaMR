"""
Event database model
"""

from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: int = Field(default=None, primary_key=True)
    name: str
    location: str
    owner_id: int = Field(foreign_key="users.id")



class EventCreate(BaseModel):
    name: str
    location: str


class EventUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
