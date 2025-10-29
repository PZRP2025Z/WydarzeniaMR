"""
Basic CRUD functionality for Event model
"""

from sqlmodel import Session, select
from app.database.models.event import Event


def create_event(db: Session, name: str, location: str) -> Event:
    event = Event(name=name, location=location)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_events(db: Session) -> list[Event]:
    return db.exec(select(Event)).all()


def get_event(db: Session, event_id: int) -> Event | None:
    return db.get(Event, event_id)


def update_event(
    db: Session, event_id: int, name: str | None = None, location: str | None = None
) -> Event | None:
    event = db.get(Event, event_id)
    if not event:
        return None
    if name is not None:
        event.name = name
    if location is not None:
        event.location = location
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event_id: int) -> bool:
    event = db.get(Event, event_id)
    if not event:
        return False
    db.delete(event)
    db.commit()
    return True
