"""
@file event_pass_service.py
@brief Logic for event pass creation and consumption.

Handles:
- Secure token generation and hashing
- Pass resolution and validation
- Guest user creation
- Pass-to-user binding
- Authentication via existing auth service
"""

import hashlib
import logging
import secrets

from fastapi import HTTPException
from sqlmodel import Session, select

from app.database.models.event_invitation import EventInvitation

logger = logging.getLogger(__name__)


def generate_invite_token() -> str:
    """
    @brief Generate a secure random token for an event invite.

    @return URL-safe token string.
    """
    return secrets.token_urlsafe(32)


def hash_invite_token(token: str) -> str:
    """
    @brief Hash an event pass token using SHA256.

    @param token Raw event pass token.

    @return Hashed token string.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_event_invite(event_id: int, db: Session) -> str:
    """
    @brief Create a new event invite for a specific event.

    @param event_id ID of the event for which the pass is created.
    @param display_name Display name for the guest user associated with the pass.
    @param db Database session dependency.
    @param expires_at Optional expiration datetime for the pass.

    @return Raw token string that can be shared with the user.
    """
    token = generate_invite_token()
    token_hash = hash_invite_token(token)
    event_invitation = EventInvitation(token_hash=token_hash, event_id=event_id)
    db.add(event_invitation)
    db.commit()
    logger.info("Invitation link for an event created")
    return token


def resolve_event_invitation(token: str, db: Session) -> EventInvitation:
    """
    @brief Resolve and validate an event invitation token.

    @param token Raw token string to resolve.
    @param db Database session dependency.

    @return EventInvitation object corresponding to the token.

    @throws HTTPException 404 if the token is invalid.
    """
    token_hash = hash_invite_token(token)
    event_pass = db.exec(
        select(EventInvitation).where(EventInvitation.token_hash == token_hash)
    ).first()
    if not event_pass:
        raise HTTPException(status_code=404, detail="Invalid pass")
    logger.info("Invitation link for an event resolved")
    return event_pass
