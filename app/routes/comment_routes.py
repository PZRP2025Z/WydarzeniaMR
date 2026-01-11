"""
comment_routes.py
=================

API routes for commenting functionality.

Provides endpoints to:
- Add a new comment to an event
- Retrieve paginated comments for an event
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.backend.comment_service import create_comment, get_comments_for_event
from app.database.models.comment import CommentCreate, CommentRead
from app.database.session import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events/{event_id}/comments", tags=["comments"])


@router.post("", response_model=CommentRead)
def add_comment(
    event_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """
    Add a new comment to a specific event.

    Creates a new comment in the database associated with the given event
    and the currently authenticated user. Logs the creation.

    Parameters:
    - event_id: ID of the event to which the comment is added
    - comment_data: CommentCreate object containing comment content
    - db: Database session
    - user: Authenticated user creating the comment

    Returns:
    - CommentRead object representing the newly created comment
    """
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
    """
    Retrieve paginated comments for a specific event.

    Fetches a list of comments for the given event, ordered by creation time descending,
    and supports pagination via limit and offset. Logs the retrieval.

    Parameters:
    - event_id: ID of the event whose comments are retrieved
    - limit: Maximum number of comments to return (default 20)
    - offset: Number of comments to skip (default 0)
    - db: Database session

    Returns:
    - List of CommentRead objects for the event
    """
    comments = get_comments_for_event(db, event_id, limit, offset)
    logger.info(f"Retrieved {len(comments)} comments for event {event_id}")
    return comments
