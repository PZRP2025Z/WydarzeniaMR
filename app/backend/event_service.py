"""
Basic CRUD functionality for Event model
"""

from sqlmodel import Session, select
from app.database.models.event import Event, EventCreate, EventUpdate


def create_event(db: Session, data: EventCreate, owner_id: int) -> Event:
    event = Event(
        name=data.name,
        location=data.location,
        time=data.time,
        description=data.description,
        photo=data.photo,
        owner_id=owner_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_events(db: Session) -> list[Event]:
    return db.exec(select(Event)).all()


def get_event(db: Session, event_id: int) -> Event | None:
    return db.get(Event, event_id)


def update_event(db: Session, event_id: int, user_id: int, data: EventUpdate):
    event = db.get(Event, event_id)
    if not event:
        return None
    if event.owner_id != user_id:
        return "forbidden"

    if data.name is not None:
        event.name = data.name
    if data.location is not None:
        event.location = data.location
    if data.time is not None:
        event.time = data.time
    if data.description is not None:
        event.description = data.description
    if data.photo is not None:
        event.photo = data.photo

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
