"""
comment_service.py
==================

Backend commenting functionality.

This module provides functions for creating comments and retrieving comments
associated with events, including user information.
"""

import logging
from sqlmodel import Session, select
from app.database.models.comment import Comment, CommentRead
from app.database.models.user import User

logger = logging.getLogger(__name__)


def create_comment(db: Session, event_id: int, user_id: int, content: str) -> CommentRead:
    """
    Create a new comment for a given event.

    :param db: Database session dependency.
    :param event_id: ID of the event to which the comment belongs.
    :param user_id: ID of the user creating the comment.
    :param content: Text content of the comment.
    :return: CommentRead object containing comment ID, user login, content, and creation timestamp.
    """
    comment = Comment(event_id=event_id, user_id=user_id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    user = db.get(User, user_id)
    response = CommentRead(
        id=comment.id,
        user_login=user.login,
        content=comment.content,
        created_at=comment.created_at,
    )
    logger.info("New comment added")
    return response


def get_comments_for_event(
    db: Session, event_id: int, limit: int = 20, offset: int = 0
) -> list[CommentRead]:
    """
    Retrieve comments for a specific event, ordered by creation time descending.

    :param db: Database session dependency.
    :param event_id: ID of the event for which to retrieve comments.
    :param limit: Maximum number of comments to return (default 20).
    :param offset: Number of comments to skip for pagination (default 0).
    :return: List of CommentRead objects including comment ID, user login, content, and creation timestamp.
    """
    stmt = (
        select(Comment)
        .where(Comment.event_id == event_id)
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    comments = db.exec(stmt).all()
    results = []
    for c in comments:
        user = db.get(User, c.user_id)
        results.append(
            CommentRead(
                id=c.id,
                user_login=user.login,
                content=c.content,
                created_at=c.created_at,
            )
        )
    logger.info(f"Got {len(results)} comments for the event")
    return results
