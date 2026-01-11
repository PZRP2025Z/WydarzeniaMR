"""
participation_service.py
========================

Backend participation survey functionality.

Provides functions for setting user participation, retrieving event participation statistics,
and listing events a user is involved with.
"""

from datetime import datetime
from sqlmodel import Session, select
from app.database.models.event import Event
from app.database.models.participations import EventParticipation, ParticipationStatus
import logging

logger = logging.getLogger(__name__)


def join_event(db: Session, *, user_id: int, event_id: int) -> EventParticipation:
    """
    Set participation status of a user as invited for a specific event.

    :param db: Database session dependency.
    :param user_id: ID of the user.
    :param event_id: ID of the event.
    :return: EventParticipation object representing the newly created participation.
    """
    return set_participation(
        db=db, user_id=user_id, event_id=event_id, status=ParticipationStatus.invited
    )


def set_participation(
    db: Session, *, user_id: int, event_id: int, status: ParticipationStatus
) -> EventParticipation:
    """
    Set or update a user's participation status for an event.

    :param db: Database session dependency.
    :param user_id: ID of the user participating in the event.
    :param event_id: ID of the event.
    :param status: ParticipationStatus enum value (going, maybe, not_going, invited).
    :return: EventParticipation object representing the updated or newly created participation.
    """
    participation = db.exec(
        select(EventParticipation).where(
            EventParticipation.user_id == user_id,
            EventParticipation.event_id == event_id,
        )
    ).first()

    if participation:
        participation.status = status
        participation.updated_at = datetime.utcnow()
    else:
        participation = EventParticipation(
            user_id=user_id,
            event_id=event_id,
            status=status,
        )
        db.add(participation)

    logger.info(f"Set participation of user {user_id} to {status} for event {event_id}")
    db.commit()
    db.refresh(participation)
    return participation


def get_event_participation_stats(db: Session, *, event_id: int) -> dict[ParticipationStatus, int]:
    """
    Retrieve statistics for an event's participation survey.

    :param db: Database session dependency.
    :param event_id: ID of the event.
    :return: Dictionary mapping ParticipationStatus to counts:
             {
                 ParticipationStatus.going: int,
                 ParticipationStatus.maybe: int,
                 ParticipationStatus.not_going: int,
                 ParticipationStatus.invited: int
             }
    """
    participants = db.exec(
        select(EventParticipation).where(EventParticipation.event_id == event_id)
    ).all()
    stats: dict[ParticipationStatus, int] = {
        ParticipationStatus.going: 0,
        ParticipationStatus.maybe: 0,
        ParticipationStatus.not_going: 0,
        ParticipationStatus.invited: 0,
    }
    for p in participants:
        stats[p.status] += 1
    return stats


def get_user_active_events(db: Session, *, user_id: int) -> list[dict]:
    """
    Get a list of events where the user is an owner or has a participation status.

    :param db: Database session dependency.
    :param user_id: ID of the user.
    :return: List of dictionaries containing event details and the user's participation status:
             [
                 {
                     "id": int,
                     "name": str,
                     "location": str,
                     "time": str (ISO format),
                     "owner_id": int,
                     "participation_status": str | None
                 },
                 ...
             ]
    """
    rows = db.exec(
        select(Event, EventParticipation)
        .join(EventParticipation, Event.id == EventParticipation.event_id, isouter=True)
        .where((Event.owner_id == user_id) | (EventParticipation.user_id == user_id))
        .order_by(Event.time)
    ).all()
    events = []
    for event, participation in rows:
        status = participation.status if participation else None
        events.append(
            {
                "id": event.id,
                "name": event.name,
                "location": event.location,
                "time": event.time.isoformat(),
                "owner_id": event.owner_id,
                "participation_status": status.name if status else None,
            }
        )
    return events
