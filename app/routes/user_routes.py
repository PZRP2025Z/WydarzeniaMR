"""
users_routes.py
=================

API endpoints for User CRUD operations.

Provides routes to:
- List all users
- Retrieve a single user
- Change user password
- Delete user account
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.backend.user_service import change_password, delete_user, get_user, get_users
from app.database.models.user import PasswordChange, UserResponse
from app.database.session import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
def read_users(db: Session = Depends(get_session)):
    """
    Retrieve all users.

    Fetches a list of all users in the database.
    """
    users = get_users(db)
    logger.info(f"Retrieved {len(users)} users from database")
    return users


@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_session)):
    """
    Retrieve a single user by ID.

    :param user_id: ID of the user to retrieve.
    :param db: Database session dependency.
    :return: UserResponse object for the specified user.
    :raises HTTPException 404: If the user does not exist.
    """
    user = get_user(db, user_id)
    if not user:
        logger.warning(f"User with id={user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"Retrieved user: id={user.id}, email={user.email}")
    return user


@router.put("/{user_id}/password")
def update_password(
    user_id: int,
    data: PasswordChange,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    Change the password for a user.

    Only the currently authenticated user can change their own password.

    :param user_id: ID of the user whose password is to be changed.
    :param data: PasswordChange object containing current and new password.
    :param db: Database session dependency.
    :param current_user: Currently authenticated user.
    :return: JSON object indicating success: {"ok": True}.
    :raises HTTPException 403: If the user attempts to change another user's password.
    :raises HTTPException 400: If the password change fails (current password incorrect or new passwords mismatch).
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can change only your own password",
        )

    success = change_password(db, user_id, data)
    if not success:
        logger.warning(f"Password change failed for user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change failed: current password may be incorrect or new passwords do not match",
        )

    logger.info(f"Password successfully changed for user_id={user_id}")
    return {"ok": True}


@router.delete("/{user_id}")
def remove_user(
    user_id: int,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    Delete a user account.

    Only the currently authenticated user can delete their own account.

    :param user_id: ID of the user to delete.
    :param db: Database session dependency.
    :param current_user: Currently authenticated user.
    :return: JSON object indicating success: {"ok": True}.
    :raises HTTPException 403: If a user attempts to delete another user's account.
    :raises HTTPException 404: If the user does not exist.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can delete only your own account",
        )

    success = delete_user(db, user_id)
    if not success:
        logger.warning(f"Failed to delete user with id={user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"Deleted user with id={user_id}")
    return {"ok": True}
