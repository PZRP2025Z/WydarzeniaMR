import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from fastapi import Body
from app.database.session import get_session
from app.backend.auth_service import get_current_user
from app.database.models.participations import ParticipationCreate
from app.backend.participations_service import (
    set_participation,
    get_event_participation_stats,
    get_user_active_events,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/participations", tags=["participations"])


@router.post("/events/{event_id}")
def participate_in_event(
    event_id: int,
    participation: ParticipationCreate,  # <- pobiera JSON
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
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
    stats = get_event_participation_stats(db, event_id=event_id)
    logger.info(f"Participation stats for event {event_id}: {stats}")
    return stats


@router.get("/me/events")
def read_my_active_events(
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    events = get_user_active_events(
        db,
        user_id=user.id,
    )

    logger.info(f"User {user.id} has {len(events)} active events")

    return events
