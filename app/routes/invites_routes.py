"""
invite_routes.py
=================

Event Invitation (reusable, account-only) API endpoints.

Provides endpoints for creating and using reusable event invitations
that require users to have an account. Multiple users can use the same invitation.
"""

import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.backend.event_invitation_service import create_event_invite, resolve_event_invitation
from app.backend.participations_service import join_event
from app.database.models.user import User
from app.database.session import get_session

load_dotenv()

router = APIRouter(prefix="/invites", tags=["invites"])
FRONTEND_BASE_URL = os.environ["FRONTEND_BASE_URL"]


class CreateInviteRequest(BaseModel):
    event_id: int


@router.post("/")
def create_invite(
    request: CreateInviteRequest,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """
    Create a reusable event invitation link.

    Generates an invitation link for the specified event. Multiple users
    can use the invitation, but they must have an account.
    """
    token = create_event_invite(event_id=request.event_id, db=db)
    return {"link": f"{FRONTEND_BASE_URL}/invite/{token}"}


@router.get("/{token}")
def open_invite(
    token: str,
    db: Session = Depends(get_session),
):
    """
    Resolve an event invitation token and return event details.

    This endpoint is public and doesn't require authentication. Returns
    basic event information so users can see what they are invited to.
    """
    invitation = resolve_event_invitation(token, db)
    return {"event_id": invitation.event_id}


@router.post("/{token}/accept")
def accept_invitation(
    token: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    Accept an event invitation with an authenticated account.

    Adds the authenticated user to the event. The invitation remains valid
    for other users to use. Logs the acceptance.
    """
    invitation = resolve_event_invitation(token, db)
    join_event(db=db, user_id=user.id, event_id=invitation.event_id)
    return {"status": "accepted", "event_id": invitation.event_id}
