"""
Basic CRUD functionality for Participations model
"""

from sqlmodel import Session, select
from datetime import datetime
from app.database.models.event import Event
from app.database.models.participations import (
    EventParticipation,
    ParticipationStatus,
)


def set_participation(
    db: Session,
    *,
    user_id: int,
    event_id: int,
    status: ParticipationStatus,
) -> EventParticipation:
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

    db.commit()
    db.refresh(participation)
    return participation


def get_event_participation_stats(
    db: Session,
    *,
    event_id: int,
) -> dict[str, int]:
    """
    Returns statistics of participations for a specific event.
    Counts how many users are going / maybe / not going.
    """
    participants = db.exec(
        select(EventParticipation).where(EventParticipation.event_id == event_id)
    ).all()

    stats = {"going": 0, "maybe": 0, "not_going": 0}
    for p in participants:
        if p.status == ParticipationStatus.going:
            stats["going"] += 1
        elif p.status == ParticipationStatus.maybe:
            stats["maybe"] += 1
        elif p.status == ParticipationStatus.not_going:
            stats["not_going"] += 1

    return stats


def get_user_active_events(
    db: Session,
    *,
    user_id: int,
) -> list[dict]:
    """
    Zwraca listę wydarzeń wraz z informacją, czy użytkownik jest właścicielem i jego statusem uczestnictwa.
    """
    # pobierz Event + EventParticipation dla tego usera
    rows = db.exec(
        select(Event, EventParticipation)
        .join(EventParticipation, Event.id == EventParticipation.event_id, isouter=True)
        .where((Event.owner_id == user_id) | (EventParticipation.user_id == user_id))
        .order_by(Event.time)
    ).all()

    # sformatuj dane tak, aby frontend mógł użyć
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
