"""
@file notification_routes.py
@brief API routes for notification preferences.

Provides endpoints to:
- Get user's notification preferences for an event
- Set/update user's notification preferences
- Bulk update notification preferences
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.backend.auth_service import get_current_user
from app.backend.notification_service import (
    get_user_notification_preferences,
    set_notification_preference,
)
from app.database.models.notifications import (
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
)
from app.database.session import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/events/{event_id}/preferences")
def get_notification_preferences(
    event_id: int,
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """
    @brief Get all notification preferences for the current user and a specific event.

    @param event_id ID of the event.
    @param db Database session dependency.
    @param user Currently authenticated user.

    @return List of NotificationPreference objects.
    """
    preferences = get_user_notification_preferences(db, user_id=user.id, event_id=event_id)
    logger.info(
        f"User {user.id} has {len(preferences)} notification preferences for event {event_id}"
    )
    return preferences


@router.post("/events/{event_id}/preferences")
def set_notification_preferences(
    event_id: int,
    preference: NotificationPreferenceCreate,
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """
    @brief Set a single notification preference for the current user and event.

    @param event_id ID of the event.
    @param preference NotificationPreferenceCreate model with type, channel, and subscribed status.
    @param db Database session dependency.
    @param user Currently authenticated user.

    @return NotificationPreference object reflecting the updated preference.
    """
    preference_obj = set_notification_preference(
        db,
        user_id=user.id,
        event_id=event_id,
        notification_type=preference.notification_type,
        channel=preference.channel,
        subscribed=preference.subscribed,
    )
    logger.info(
        f"User {user.id} set notification preference for event {event_id}: "
        f"{preference.notification_type.value}/{preference.channel.value} = {preference.subscribed}"
    )
    return preference_obj


@router.put("/events/{event_id}/preferences")
def bulk_update_notification_preferences(
    event_id: int,
    updates: NotificationPreferenceUpdate,
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    """
    @brief Bulk update multiple notification preferences for the current user and event.

    Allows setting multiple preferences in a single request

    @param event_id ID of the event.
    @param updates NotificationPreferenceUpdate model with list of preferences.
    @param db Database session dependency.
    @param user Currently authenticated user.

    @return List of updated NotificationPreference objects.
    """
    if user.is_guest:
        raise HTTPException(status_code=403, detail="Guest users cannot receive notifications")
    results = []
    for pref in updates.preferences:
        preference_obj = set_notification_preference(
            db,
            user_id=user.id,
            event_id=event_id,
            notification_type=pref.notification_type,
            channel=pref.channel,
            subscribed=pref.subscribed,
        )
        results.append(preference_obj)

    logger.info(
        f"User {user.id} updated {len(results)} notification preferences for event {event_id}"
    )
    return results
