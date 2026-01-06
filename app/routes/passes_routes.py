"""
@file passes_routes.py
@brief Event Pass (magic link) API endpoints.

This module provides endpoints for creating and consuming event-specific
pass links that allow passwordless access for guest users and controlled
linking to registered user accounts.
"""

import os

from dotenv import load_dotenv
from fastapi import APIRouter, Body, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.backend.event_pass_service import (
    bind_pass_to_user,
    create_event_pass,
    create_guest_user,
    login_via_pass,
    resolve_event_pass,
)
from app.database.models.user import User
from app.database.session import get_session


class CreatePassRequest(BaseModel):
    display_name: str


load_dotenv()

router = APIRouter(prefix="/passes", tags=["passes"])
FRONTEND_BASE_URL = os.environ["FRONTEND_BASE_URL"]


@router.post("/personal/{event_id}")
def create_pass(
    event_id: int,
    request: CreatePassRequest = Body(...),
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """
    @brief Create a personal event pass.

    Generates an event pass link for the specified event.
    The pass is initially unbound and can later be claimed by a guest
    or linked to an existing user account.

    @param event_id ID of the event the pass grants access to.
    @param display_name Display name for the guest user.
    @param db Database session dependency.
    @param user Authenticated user creating the pass.

    @return JSON object containing the frontend pass URL.

    @throws HTTPException 401 if user is not authenticated.
    """
    token = create_event_pass(
        event_id=event_id,
        display_name=request.display_name,
        db=db,
    )

    return {"link": f"{FRONTEND_BASE_URL}/pass/{token}"}


@router.get("/{token}")
def open_pass(
    token: str,
    response: Response,
    db: Session = Depends(get_session),
):
    """
    @brief Resolve an event pass token.

    Determines the state of the pass and the required next action.
    If the pass is bound to a guest user, the user is automatically logged in.
    If bound to a registered user, explicit login is required.

    @param token Event pass token from the URL.
    @param response FastAPI response object used to set auth cookies.
    @param db Database session dependency.

    @return JSON describing pass state:
            - logged_in
            - unbound
            - login_required

    @throws HTTPException 401 if the bound user does not exist.
    @throws HTTPException 404 if the pass token is invalid.
    """
    event_pass = resolve_event_pass(token, db)

    if event_pass.user_id:
        user = db.get(User, event_pass.user_id)

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if not user.is_guest:
            return {"status": "login_required", "event_id": event_pass.event_id}

        login_via_pass(event_pass=event_pass, response=response, db=db)
        return {"status": "logged_in", "event_id": event_pass.event_id}

    return {
        "status": "unbound",
        "event_id": event_pass.event_id,
        "display_name": event_pass.display_name,
    }


@router.post("/{token}/accept-guest")
def accept_as_guest(
    token: str,
    response: Response,
    db: Session = Depends(get_session),
):
    """
    @brief Accept an event pass as a guest user.

    Creates a new guest user, binds the pass to that user,
    and logs the user in. If the pass is already bound,
    the existing user is logged in instead.

    @param token Event pass token.
    @param response FastAPI response object used to set auth cookies.
    @param db Database session dependency.

    @return JSON indicating whether a guest was created or already logged in.

    @throws HTTPException 404 if the pass token is invalid.
    """
    event_pass = resolve_event_pass(token, db)

    if event_pass.user_id:
        login_via_pass(event_pass=event_pass, response=response, db=db)
        return {"status": "logged_in"}

    user = create_guest_user(event_pass.display_name, db)
    bind_pass_to_user(event_pass, user, db)
    login_via_pass(event_pass=event_pass, response=response, db=db)

    return {"status": "guest_created"}


@router.post("/{token}/accept-login")
def accept_with_existing_login(
    token: str,
    response: Response,
    user=Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    @brief Bind an event pass to an authenticated user.

    Links the event pass to the currently authenticated user.

    @param token Event pass token.
    @param response FastAPI response object used to set auth cookies.
    @param user Currently authenticated user.
    @param db Database session dependency.

    @return JSON confirming successful linking.

    @throws HTTPException 401 if the user is not authenticated.
    @throws HTTPException 404 if the pass token is invalid.
    """
    event_pass = resolve_event_pass(token, db)
    bind_pass_to_user(event_pass, user, db)

    return {"status": "linked"}
