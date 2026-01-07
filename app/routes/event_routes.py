"""
@file event_routes.py
@brief API routes for Event CRUD operations.

Provides endpoints to:
- Create a new event
- Retrieve all events or a single event by ID
- Update an existing event
- Delete an event
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.backend.event_service import (
    create_event,
    delete_event,
    get_event,
    get_events,
    update_event,
)
from app.database.models.event import EventCreate, EventUpdate
from app.database.session import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/")
def add_event(
    event_data: EventCreate,
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """
    @brief Create a new event.

    Adds a new event to the database with the currently authenticated user
    set as the owner.

    @param event_data EventCreate model with event details.
    @param db Database session dependency.
    @param user Currently authenticated user.

    @return The newly created Event model.
    """
    return create_event(db, event_data, owner_id=user.id)


@router.get("/")
def read_events(db: Session = Depends(get_session)):
    """
    @brief Retrieve all events.

    Fetches a list of all events from the database.

    @param db Database session dependency.

    @return List of Event models.
    """
    events = get_events(db)
    logger.info(f"Retrieved {len(events)} events from database")
    return events


@router.get("/{event_id}")
def read_event(event_id: int, db: Session = Depends(get_session)):
    """
    @brief Retrieve a single event by its ID.

    Fetches the event details from the database. Raises 404 if not found.

    @param event_id ID of the event to retrieve.
    @param db Database session dependency.

    @return Event model corresponding to the given ID.
    @throws HTTPException 404 if the event is not found.
    """
    event = get_event(db, event_id)
    if not event:
        logger.warning(f"Event with id={event_id} not found")
        raise HTTPException(status_code=404, detail="Event not found")
    logger.info(f"Retrieved event: id={event.id}, name={event.name}")
    return event


@router.put("/{event_id}")
def edit_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """
    @brief Update an existing event.

    Allows the owner of the event to update its details. Raises 403 if
    the user is not the owner, 404 if the event does not exist.

    @param event_id ID of the event to update.
    @param event_data EventUpdate model with updated fields.
    @param db Database session dependency.
    @param user Currently authenticated user.

    @return Updated Event model.
    @throws HTTPException 403 if the user is not the owner.
    @throws HTTPException 404 if the event does not exist.
    """
    event = update_event(db, event_id, user.id, event_data)

    if event is None:
        raise HTTPException(404, "Event not found")
    if event == "forbidden":
        raise HTTPException(403, "You are not the owner of this event")

    return event


@router.delete("/{event_id}")
def remove_event(
    event_id: int,
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """
    @brief Delete an existing event.

    Allows the owner of the event to delete it. Raises 403 if the user
    is not the owner, 404 if the event does not exist.

    @param event_id ID of the event to delete.
    @param db Database session dependency.
    @param user Currently authenticated user.

    @return JSON confirming deletion: {"ok": True}.
    @throws HTTPException 403 if the user is not the owner.
    @throws HTTPException 404 if the event does not exist.
    """
    result = delete_event(db, event_id, user_id=user.id)

    if result is False:
        raise HTTPException(404, "Event not found")
    if result == "forbidden":
        raise HTTPException(403, "You are not the owner of this event")

    return {"ok": True}
