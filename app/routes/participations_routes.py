"""
@file participation_routes.py
@brief API routes for participation survey functionality.

Provides endpoints to:
- Set a user's participation status for an event
- Retrieve participation statistics for an event
- Get a list of events where the user is participating or is the owner
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
    participation: ParticipationCreate,  # <- pobiera JSON
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """
    @brief Set participation status for a user in an event.

    Updates or creates the participation record for the authenticated user
    for the specified event.

    @param event_id ID of the event.
    @param participation ParticipationCreate model with status (going/maybe/not_going).
    @param db Database session dependency.
    @param user Currently authenticated user.

    @return EventParticipation model reflecting the user's participation status.
    """
    participation_obj = set_participation(
        db,
        user_id=user.id,
        event_id=event_id,
        status=participation.status,
    )
    return participation_obj


@router.get("/events/{event_id}/stats")
def read_event_participation_stats(
    event_id: int,
    db: Session = Depends(get_session),
):
    """
    @brief Retrieve participation statistics for a specific event.

    Counts how many users are going, maybe, or not going to the event.

    @param event_id ID of the event.
    @param db Database session dependency.

    @return Dictionary with participation counts: {"going": int, "maybe": int, "not_going": int}.
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
    @brief Get a list of events the current user is participating in or owns.

    Includes events where the user has a participation record or is the event owner.

    @param db Database session dependency.
    @param user Currently authenticated user.

    @return List of events with participation status, e.g.:
            [{"id": int, "name": str, "location": str, "time": str,
              "owner_id": int, "participation_status": str | None}, ...]
    """
    events = get_user_active_events(
        db,
        user_id=user.id,
    )

    logger.info(f"User {user.id} has {len(events)} active events")

    return events
