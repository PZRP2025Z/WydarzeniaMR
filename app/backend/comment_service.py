from sqlmodel import Session, select
from app.database.models.comment import Comment


def create_comment(db: Session, event_id: int, user_id: int, content: str) -> Comment:
    comment = Comment(event_id=event_id, user_id=user_id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comments_for_event(
    db: Session, event_id: int, limit: int = 20, offset: int = 0
) -> list[Comment]:
    stmt = (
        select(Comment)
        .where(Comment.event_id == event_id)
        .order_by(Comment.created_at)
        .limit(limit)
        .offset(offset)
    )
    return db.exec(stmt).all()
