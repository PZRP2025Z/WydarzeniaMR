"""
Router for event CRUD service
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database.session import get_session
from app.backend.event_service import (
    create_event,
    get_events,
    get_event,
    update_event,
    delete_event,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/")
def add_event(name: str, location: str, db: Session = Depends(get_session)):
    return create_event(db, name, location)


@router.get("/")
def read_events(db: Session = Depends(get_session)):
    return get_events(db)


@router.get("/{event_id}")
def read_event(event_id: int, db: Session = Depends(get_session)):
    event = get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}")
def edit_event(
    event_id: int,
    name: str | None = None,
    location: str | None = None,
    db: Session = Depends(get_session),
):
    event = update_event(db, event_id, name, location)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/{event_id}")
def remove_event(event_id: int, db: Session = Depends(get_session)):
    success = delete_event(db, event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"ok": True}
