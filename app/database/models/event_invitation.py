"""
event_invitation.py
===================

Database models for invitation link related activities.

Provides SQLModel table for storing event invites for users, including token hash and event association.
"""

from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class EventInvitation(SQLModel, table=True):
    """
    Database table model representing an event invitation link.

    :param id: Primary key of the event pass.
    :param token_hash: SHA-256 hash of the pass token (unique, indexed).
    :param event_id: ID of the event the pass grants access to.
    :param created_at: Timestamp when the pass was created (UTC).
    """

    __tablename__ = "event_invitations"
    id: int | None = Field(default=None, primary_key=True)
    token_hash: str = Field(index=True, unique=True)
    event_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
