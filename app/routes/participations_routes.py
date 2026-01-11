"""
participation_routes.py
=======================

API routes for participation survey functionality.

This module provides endpoints for:
- Setting a user's participation status for an event
- Retrieving participation statistics for an event
- Listing events where the user is participating or is the owner
"""

import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.backend.participations_service import (
    get_event_participation_stats,
    get_user_active_events,
    set_participation,
)
from app.database.models.participations import ParticipationCreate
from app.database.session import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/participations", tags=["participations"])


@router.post("/events/{event_id}")
def participate_in_event(
    event_id: int,
    participation: ParticipationCreate,
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """
    Set participation status for a user in an event.

    Updates or creates the participation record for the authenticated user
    for the specified event.

    Parameters:
    - event_id: ID of the event
    - participation: ParticipationCreate object with status (going/maybe/not_going)
    - db: Database session
    - user: Currently authenticated user

    Returns:
    - EventParticipation object reflecting the user's participation status
    """
    participation_obj = set_participation(
        db,
        user_id=user.id,
        event_id=event_id,
        status=participation.status,
    )
    logger.info(f"User {user.id} set participation '{participation.status}' for event {event_id}")
    return participation_obj


@router.get("/events/{event_id}/stats")
def read_event_participation_stats(
    event_id: int,
    db: Session = Depends(get_session),
):
    """
    Retrieve participation statistics for a specific event.

    Counts how many users are going, maybe, or not going to the event.

    Parameters:
    - event_id: ID of the event
    - db: Database session

    Returns:
    - Dictionary with participation counts, e.g. {"going": int, "maybe": int, "not_going": int}
    """
    stats = get_event_participation_stats(db, event_id=event_id)
    logger.info(f"Participation stats for event {event_id}: {stats}")
    return stats


@router.get("/me/events")
def read_my_active_events(
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """
    Get a list of events the current user is participating in or owns.

    Includes events where the user has a participation record or is the event owner.

    Parameters:
    - db: Database session
    - user: Currently authenticated user

    Returns:
    - List of events with participation status, e.g.:
      [{"id": int, "name": str, "location": str, "time": str,
        "owner_id": int, "participation_status": str | None}, ...]
    """
    events = get_user_active_events(
        db,
        user_id=user.id,
    )
    logger.info(f"User {user.id} has {len(events)} active events")
    return events
