"""
@file invite_routes.py
@brief Event Invitation (reusable, account-only) API endpoints.

This module provides endpoints for creating and using reusable event invitations
that require users to have an account. Multiple users can use the same invitation.
"""

import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.backend.event_invitation_service import (
    create_event_invite,
    resolve_event_invitation,
)
from app.backend.participations_service import join_event
from app.database.models.user import User
from app.database.session import get_session


class CreateInviteRequest(BaseModel):
    event_id: int


load_dotenv()

router = APIRouter(prefix="/invites", tags=["invites"])
FRONTEND_BASE_URL = os.environ["FRONTEND_BASE_URL"]


@router.post("/")
def create_invite(
    request: CreateInviteRequest,
    db: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """
    @brief Create a reusable event invitation link.

    Generates an invitation link for the specified event.
    The invitation can be used by multiple users, but requires an account.

    @param request Contains event_id for which to create the invitation.
    @param db Database session dependency.
    @param user Authenticated user creating the invitation.

    @return JSON object containing the frontend invitation URL.

    @throws HTTPException 401 if user is not authenticated.
    """
    token = create_event_invite(
        event_id=request.event_id,
        db=db,
    )

    return {"link": f"{FRONTEND_BASE_URL}/invite/{token}"}


@router.get("/{token}")
def open_invite(
    token: str,
    db: Session = Depends(get_session),
):
    """
    @brief Resolve an event invitation token and return event details.

    This endpoint is public and doesn't require authentication.
    Returns event information so users can see what they're being invited to.

    @param token Event invitation token from the URL.
    @param db Database session dependency.

    @return JSON with event_id.

    @throws HTTPException 404 if the invitation token is invalid.
    @throws HTTPException 410 if the invitation has expired.
    """
    invitation = resolve_event_invitation(token, db)

    return {
        "event_id": invitation.event_id,
    }


@router.post("/{token}/accept")
def accept_invitation(
    token: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    @brief Accept an event invitation with an authenticated account.

    Adds the authenticated user to the event. The invitation remains valid
    for other users to use.

    @param token Event invitation token.
    @param user Currently authenticated user.
    @param db Database session dependency.

    @return JSON confirming successful acceptance with event_id.

    @throws HTTPException 401 if the user is not authenticated.
    @throws HTTPException 404 if the invitation token is invalid.
    @throws HTTPException 410 if the invitation has expired.
    """
    invitation = resolve_event_invitation(token, db)
    join_event(db=db, user_id=user.id, event_id=invitation.event_id)

    return {"status": "accepted", "event_id": invitation.event_id}
