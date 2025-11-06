"""
Event database model
"""

from sqlmodel import SQLModel, Field


class Event(SQLModel, table=True):
    __tablename__ = "events"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    location: str
