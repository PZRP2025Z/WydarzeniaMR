"""
@file event_service.py
@brief Backend event CRUD operations.

Provides functions to create, read, update, and delete events in the database.
"""

from sqlmodel import Session, select

from app.database.models.event import Event, EventCreate, EventUpdate


def create_event(db: Session, data: EventCreate, owner_id: int) -> Event:
    """
    @brief Create a new event in the database.

    @param db Database session dependency.
    @param data EventCreate object containing event details.
    @param owner_id ID of the user creating the event.

    @return Newly created Event object.
    """
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
    """
    @brief Retrieve all events from the database.

    @param db Database session dependency.

    @return List of Event objects.
    """
    return db.exec(select(Event)).all()


def get_event(db: Session, event_id: int) -> Event | None:
    """
    @brief Retrieve a single event by its ID.

    @param db Database session dependency.
    @param event_id ID of the event to retrieve.

    @return Event object if found, None otherwise.
    """
    return db.get(Event, event_id)


def update_event(db: Session, event_id: int, user_id: int, data: EventUpdate) -> Event:
    """
    @brief Update an existing event's details.

    @param db Database session dependency.
    @param event_id ID of the event to update.
    @param user_id ID of the user attempting the update.
    @param data EventUpdate object containing new values.

    @return Updated Event object if successful, "forbidden" if the user is not the owner,
            or None if the event does not exist.
    """
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


def delete_event(db: Session, event_id: int, user_id: int) -> bool:
    """
    @brief Delete an event from the database.

    @param db Database session dependency.
    @param event_id ID of the event to delete.
    @param user_id ID of the user attempting the deletion.

    @return True if deleted successfully, "forbidden" if user is not the owner,
            False if the event does not exist.
    """
    event = db.get(Event, event_id)
    if not event:
        return False
    if event.owner_id != user_id:
        return "forbidden"
    db.delete(event)
    db.commit()
    return True
