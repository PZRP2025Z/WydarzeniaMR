"""
comment_models.py
=================

Database models for comments-related activities.

Provides SQLModel and Pydantic models for creating, reading, and storing comments
associated with events and users.
"""

from datetime import datetime
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class Comment(SQLModel, table=True):
    """
    Database table model representing a comment.

    :param id: Primary key of the comment.
    :param event_id: Foreign key referencing the related event.
    :param user_id: Foreign key referencing the author user.
    :param content: Text content of the comment.
    :param created_at: Timestamp when the comment was created.
    """

    __tablename__ = "comments"
    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    content: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CommentCreate(BaseModel):
    """
    Pydantic model for creating a new comment.

    :param content: Text content of the comment.
    """

    content: str


class CommentRead(BaseModel):
    """
    Pydantic model for reading a comment.

    :param id: Primary key of the comment.
    :param user_login: Login/username of the comment author.
    :param content: Text content of the comment.
    :param created_at: Timestamp when the comment was created.
    """

    id: int
    user_login: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
