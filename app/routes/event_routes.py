import logging
from fastapi import APIRouter, Depends, HTTPException
from app.database.models.event import EventCreate, EventUpdate
from sqlmodel import Session
from app.database.session import get_session
from app.backend.auth_service import get_current_user
from app.backend.event_service import (
    create_event,
    get_events,
    get_event,
    update_event,
    delete_event,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/")
def add_event(
    event_data: EventCreate,
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    event = create_event(db, event_data.name, event_data.location)
    logger.info(
        f"User {user.id} created event: id={event.id}, name={event.name}, location={event.location}"
    )
    return event


@router.get("/")
def read_events(db: Session = Depends(get_session)):
    events = get_events(db)
    logger.info(f"Retrieved {len(events)} events from database")
    return events


@router.get("/{event_id}")
def read_event(event_id: int, db: Session = Depends(get_session)):
    event = get_event(db, event_id)
    if not event:
        logger.warning(f"Event with id={event_id} not found")
        raise HTTPException(status_code=404, detail="Event not found")
    logger.info(f"Retrieved event: id={event.id}, name={event.name}")
    return event


@router.put("/{event_id}")
def edit_event(
    event_id: int, event_data: EventUpdate, db: Session = Depends(get_session)
):
    event = update_event(
        db, event_id, name=event_data.name, location=event_data.location
    )
    if not event:
        logger.warning(f"Failed to update event with id={event_id}")
        raise HTTPException(status_code=404, detail="Event not found")
    logger.info(
        f"Updated event: id={event.id}, name={event.name}, location={event.location}"
    )
    return event


@router.delete("/{event_id}")
def remove_event(event_id: int, db: Session = Depends(get_session)):
    success = delete_event(db, event_id)
    if not success:
        logger.warning(f"Failed to delete event with id={event_id}")
        raise HTTPException(status_code=404, detail="Event not found")
    logger.info(f"Deleted event with id={event_id}")
    return {"ok": True}
