"""
Basic CRUD functionality for Event model
"""

from sqlmodel import Session, select
from app.database.models.event import Event


def create_event(db: Session, name: str, location: str, owner_id: int) -> Event:
    event = Event(name=name, location=location, owner_id=owner_id)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_events(db: Session) -> list[Event]:
    return db.exec(select(Event)).all()


def get_event(db: Session, event_id: int) -> Event | None:
    return db.get(Event, event_id)


def update_event(
    db: Session,
    event_id: int,
    user_id: int,
    name: str | None = None,
    location: str | None = None,
) -> Event | None:
    event = db.get(Event, event_id)
    if not event:
        return None
    if event.owner_id != user_id:
        return "forbidden"

    if name is not None:
        event.name = name
    if location is not None:
        event.location = location

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event_id: int, user_id: int) -> bool | str:
    event = db.get(Event, event_id)
    if not event:
        return False
    if event.owner_id != user_id:
        return "forbidden"

    db.delete(event)
    db.commit()
    return True
