import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from app.database.session import get_session
from app.backend.comment_service import create_comment, get_comments_for_event
from app.database.models.comment import CommentCreate, CommentRead
from app.backend.auth_service import get_current_user  # <-- masz to w auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events/{event_id}/comments", tags=["comments"])


@router.post("", response_model=CommentRead)
def add_comment(
    event_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """Add a comment to an event."""
    comment = create_comment(db, event_id=event_id, user_id=user.id, content=comment_data.content)
    logger.info(f"User {user.id} added comment {comment.id} to event {event_id}")
    return comment


@router.get("", response_model=list[CommentRead])
def read_comments(
    event_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
):
    comments = get_comments_for_event(db, event_id, limit, offset)
    logger.info(f"Retrieved {len(comments)} comments for event {event_id}")
    return comments
