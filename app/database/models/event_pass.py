"""
event_pass_models.py
===================

Database models for invitation link (event pass) related activities.

Provides SQLModel table for storing event passes (magic links) for guests
and users, including token hash, event association, and display name.
"""

from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class EventPass(SQLModel, table=True):
    """
    Database table model representing an event pass (invitation link).

    :param id: Primary key of the event pass.
    :param token_hash: SHA-256 hash of the pass token (unique, indexed).
    :param event_id: ID of the event the pass grants access to.
    :param user_id: Optional ID of the user bound to the pass.
    :param display_name: Display name of the guest or user associated with the pass.
    :param created_at: Timestamp when the pass was created (UTC).
    """

    __tablename__ = "event_passes"
    id: int | None = Field(default=None, primary_key=True)
    token_hash: str = Field(index=True, unique=True)
    event_id: int = Field(index=True)
    user_id: int | None = Field(default=None, foreign_key="users.id")
    display_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
