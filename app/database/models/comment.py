"""
Comment database model
"""

from datetime import datetime
from sqlmodel import SQLModel, Field, Index
from pydantic import BaseModel


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (Index("idx_event_created", "event_id", "created_at"),)


class CommentCreate(BaseModel):
    content: str


class CommentRead(BaseModel):
    id: int
    user_login: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
