import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

from app.database.session import get_session
from app.database.models.user import UserResponse, PasswordChange
from app.backend.user_service import get_users, get_user, change_password, delete_user
from app.backend.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
def read_users(db: Session = Depends(get_session)):
    users = get_users(db)
    logger.info(f"Retrieved {len(users)} users from database")
    return users


@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_session)):
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
    # zabezpieczenie: user może zmienić tylko swoje hasło
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
