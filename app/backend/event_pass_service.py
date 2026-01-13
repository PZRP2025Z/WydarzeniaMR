"""
event_pass_service.py
=====================

Logic for event pass creation and consumption.

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

from fastapi import HTTPException, Response
from sqlmodel import Session, select

from app.backend.auth_service import issue_tokens_and_set_cookies
from app.backend.participations_service import join_event
from app.database.models.event_pass import EventPass
from app.database.models.user import User

logger = logging.getLogger(__name__)


def generate_pass_token() -> str:
    """
    Generate a secure random token for an event pass.

    :return: URL-safe token string.
    """
    return secrets.token_urlsafe(32)


def hash_pass_token(token: str) -> str:
    """
    Hash an event pass token using SHA256.

    :param token: Raw event pass token.
    :return: Hashed token string.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_event_pass(event_id: int, display_name: str, db: Session, expires_at=None) -> str:
    """
    Create a new event pass for a specific event.

    :param event_id: ID of the event for which the pass is created.
    :param display_name: Display name for the guest user associated with the pass.
    :param db: Database session dependency.
    :param expires_at: Optional expiration datetime for the pass.
    :return: Raw token string that can be shared with the user.
    """
    token = generate_pass_token()
    token_hash = hash_pass_token(token)
    event_pass = EventPass(
        token_hash=token_hash,
        event_id=event_id,
        display_name=display_name,
        expires_at=expires_at,
    )
    db.add(event_pass)
    db.commit()
    logger.info("Invitation link for an event created")
    return token


def resolve_event_pass(token: str, db: Session) -> EventPass:
    """
    Resolve and validate an event pass token.

    :param token: Raw token string to resolve.
    :param db: Database session dependency.
    :return: EventPass object corresponding to the token.
    :raises HTTPException: 404 if the token is invalid.
    """
    token_hash = hash_pass_token(token)
    event_pass = db.exec(select(EventPass).where(EventPass.token_hash == token_hash)).first()
    if not event_pass:
        raise HTTPException(status_code=404, detail="Invalid pass")
    logger.info(f"Invitation link for an event {event_pass.event_id} resolved")
    return event_pass


def create_guest_user(display_name: str, db: Session) -> User:
    """
    Create a new guest user.

    :param display_name: Display name for the guest user.
    :param db: Database session dependency.
    :return: Newly created User object with is_guest=True.
    """
    user = User(
        login=display_name,
        email=f"guest_{secrets.token_hex(8)}@guest.local",
        is_guest=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Guest user created")
    return user


def bind_pass_to_user(event_pass: EventPass, user: User, db: Session) -> None:
    """
    Bind an event pass to a specific user.

    :param event_pass: EventPass object to bind.
    :param user: User object to bind the pass to.
    :param db: Database session dependency.
    :raises HTTPException: 409 if the pass is already bound to another user.
    """
    db.refresh(event_pass)
    if event_pass.user_id and event_pass.user_id != user.id:
        raise HTTPException(status_code=409, detail="Pass already bound to another user")
    if event_pass.user_id:
        return
    event_pass.user_id = user.id
    db.commit()
    db.refresh(event_pass)
    join_event(db=db, user_id=user.id, event_id=event_pass.event_id)
    logger.info("Invitation link bound to a user")


def login_via_pass(*, event_pass: EventPass, response: Response, db: Session) -> None:
    """
    Log in a user via an existing event pass.

    :param event_pass: EventPass object representing the pass.
    :param response: FastAPI Response object used to set authentication cookies.
    :param db: Database session dependency.
    :raises HTTPException: 400 if the pass is not bound to a user.
    :raises HTTPException: 401 if the user associated with the pass does not exist.
    """
    if not event_pass.user_id:
        raise HTTPException(status_code=400, detail="Pass not bound")
    user = db.get(User, event_pass.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    issue_tokens_and_set_cookies(user, response)
    logger.info("User logged in via invitation link")
