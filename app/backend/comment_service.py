from sqlmodel import Session, select
from app.database.models.comment import Comment
from app.database.models.user import User
from app.database.models.comment import CommentRead


def create_comment(
    db: Session, event_id: int, user_id: int, content: str
) -> CommentRead:
    comment = Comment(event_id=event_id, user_id=user_id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    user = db.get(User, user_id)

    return CommentRead(
        id=comment.id,
        user_login=user.login,
        content=comment.content,
        created_at=comment.created_at,
    )


def get_comments_for_event(
    db: Session, event_id: int, limit: int = 20, offset: int = 0
) -> list[CommentRead]:
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

    return results
