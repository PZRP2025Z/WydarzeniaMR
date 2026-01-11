"""
user_service.py
================

Basic functionality for the User model.

Provides functions to retrieve users, change passwords, and delete users.
"""

from sqlmodel import Session, select
from app.backend.auth_service import get_password_hash, verify_password
from app.database.models.user import PasswordChange, User


def get_users(db: Session) -> list[User]:
    """
    Retrieve all users from the database.

    :param db: Database session dependency.
    :return: List of User objects.
    """
    return db.exec(select(User)).all()


def get_user(db: Session, user_id: int) -> User | None:
    """
    Retrieve a single user by their ID.

    :param db: Database session dependency.
    :param user_id: ID of the user to retrieve.
    :return: User object if found, None otherwise.
    """
    return db.get(User, user_id)


def change_password(db: Session, user_id: int, data: PasswordChange) -> bool:
    """
    Change the password of a user after verifying the current password.

    :param db: Database session dependency.
    :param user_id: ID of the user whose password is being changed.
    :param data: PasswordChange object containing current and new passwords.
    :return: True if password was changed successfully, False otherwise
             (invalid current password, mismatch in new password confirmation, or user not found).
    """
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


def delete_user(db: Session, user_id: int) -> bool:
    """
    Delete a user from the database.

    :param db: Database session dependency.
    :param user_id: ID of the user to delete.
    :return: True if deleted successfully, False if user does not exist.
    """
    user = db.get(User, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
