"""
Event database model
"""

from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class Event(SQLModel, table=True):
    __tablename__ = "events"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    location: str


class EventCreate(BaseModel):
    name: str
    location: str


class EventUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
