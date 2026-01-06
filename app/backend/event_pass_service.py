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
import secrets

from fastapi import HTTPException, Response
from pydantic import BaseModel
from sqlmodel import Session, select

from app.backend.auth_service import issue_tokens_and_set_cookies
from app.database.models.event_pass import EventPass
from app.database.models.user import User


def generate_pass_token() -> str:
    return secrets.token_urlsafe(32)


def hash_pass_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_event_pass(
    event_id: int,
    display_name: str,
    db: Session,
    expires_at=None,
) -> str:
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

    return token


def resolve_event_pass(token: str, db: Session) -> EventPass:
    token_hash = hash_pass_token(token)

    event_pass = db.exec(select(EventPass).where(EventPass.token_hash == token_hash)).first()

    if not event_pass:
        raise HTTPException(status_code=404, detail="Invalid pass")

    return event_pass


def create_guest_user(display_name: str, db: Session) -> User:
    user = User(
        login=display_name,
        is_guest=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def bind_pass_to_user(
    event_pass: EventPass,
    user: User,
    db: Session,
):
    db.refresh(event_pass)
    if event_pass.user_id and event_pass.user_id != user.id:
        raise HTTPException(status_code=409, detail="Pass already bound to another user")

    if event_pass.user_id:
        return

    event_pass.user_id = user.id
    db.add(event_pass)
    db.commit()


def login_via_pass(
    *,
    event_pass: EventPass,
    response: Response,
    db: Session,
):
    if not event_pass.user_id:
        raise HTTPException(status_code=400, detail="Pass not bound")

    user = db.get(User, event_pass.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    issue_tokens_and_set_cookies(user, response)
