"""
user_service.py
================

Basic functionality for the User model.

Provides functions to retrieve users, change passwords, and delete users.
"""

import logging

from sqlmodel import Session, select
from app.backend.auth_service import get_password_hash, verify_password
from app.database.models.user import PasswordChange, User, UserEmailInfo

logger = logging.getLogger(__name__)


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


def get_user_emails_by_ids(
    db: Session, user_ids: list[int], include_guests: bool = False
) -> dict[int, UserEmailInfo]:
    """
    @brief Fetch email addresses and usernames for multiple users by their IDs.

    @param db Database session dependency.
    @param user_ids List of user IDs to fetch emails for.
    @param include_guests Whether to include guest users in the results (default: False).

    @return Dictionary mapping user_id to UserEmailInfo (containing email and login).
            Users without valid emails are excluded from the result.
            Guest users are excluded unless include_guests is True.
    """
    if not user_ids:
        return {}

    query = select(User.id, User.email, User.login).where(User.id.in_(user_ids))

    if not include_guests:
        query = query.where(User.is_guest == False)

    users = db.exec(query).all()

    email_map = {
        user_id: UserEmailInfo(email=email, login=login) for user_id, email, login in users if email
    }

    logger.info(
        f"Fetched {len(email_map)} email addresses for {len(user_ids)} user IDs (include_guests={include_guests})"
    )

    missing = set(user_ids) - set(email_map.keys())
    if missing:
        logger.warning(f"Could not find emails for user IDs: {missing}")

    return email_map
