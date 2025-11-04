"""
Basic CRUD functionality for User model
"""

from typing import Optional, List
from sqlmodel import Session, select
from app.database.models.user import User, PasswordChange
from app.backend.auth_service import verify_password, get_password_hash


def get_users(db: Session) -> List[User]:
    return db.exec(select(User)).all()


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def change_password(db: Session, user_id: int, data: PasswordChange) -> bool:
    user = db.get(User, user_id)
    if not user:
        return False

    if not verify_password(data.current_password, user.hashed_password):
        return False

    if data.new_password != data.new_password_confirm:
        return False

    user.hashed_password = get_password_hash(data.new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return True
