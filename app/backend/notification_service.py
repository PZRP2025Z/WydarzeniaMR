"""
@file notification_service.py
@brief Backend notification functionality.

Provides functions for managing notification preferences and gathering
subscribers for sending notifications.
"""

import logging
from datetime import datetime

from sqlmodel import Session, select

from app.backend.tasks.tasks import send_email_notifications
from app.backend.user_service import get_user_emails_by_ids, get_user
from app.database.models.notifications import (
    NotificationChannel,
    NotificationPreference,
    NotificationType,
)

logger = logging.getLogger(__name__)


def set_notification_preference(
    db: Session,
    *,
    user_id: int,
    event_id: int,
    notification_type: NotificationType,
    channel: NotificationChannel,
    subscribed: bool,
) -> NotificationPreference:
    """
    @brief Set or update a user's notification preference for an event.

    @param db Database session dependency.
    @param user_id ID of the user.
    @param event_id ID of the event.
    @param notification_type Type of notification (event_updated, participant_joined).
    @param channel Delivery channel (email).
    @param subscribed Whether to subscribe or unsubscribe.

    @return NotificationPreference object representing the updated or newly created preference.
    """
    preference = db.exec(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.event_id == event_id,
            NotificationPreference.notification_type == notification_type,
            NotificationPreference.channel == channel,
        )
    ).first()

    if preference:
        preference.subscribed = subscribed
    else:
        preference = NotificationPreference(
            user_id=user_id,
            event_id=event_id,
            notification_type=notification_type,
            channel=channel,
            subscribed=subscribed,
        )
        db.add(preference)

    logger.info(
        f"Set notification preference for user {user_id}, event {event_id}: "
        f"{notification_type.value}/{channel.value} = {subscribed}"
    )
    db.commit()
    db.refresh(preference)
    return preference


def get_user_notification_preferences(
    db: Session, *, user_id: int, event_id: int
) -> list[NotificationPreference]:
    """
    @brief Get all notification preferences for a user and event.

    @param db Database session dependency.
    @param user_id ID of the user.
    @param event_id ID of the event.

    @return List of NotificationPreference objects.
    """
    preferences = db.exec(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.event_id == event_id,
        )
    ).all()
    return list(preferences)


def get_notification_subscribers(
    db: Session,
    *,
    event_id: int,
    notification_type: NotificationType,
    channel: NotificationChannel,
) -> list[int]:
    """
    @brief Get list of user IDs subscribed to a specific notification type and channel for an event.

    @param db Database session dependency.
    @param event_id ID of the event.
    @param notification_type Type of notification (event_updated, participant_joined).
    @param channel Delivery channel (email).

    @return List of user IDs who are subscribed to this specific channel.
    """
    subscribers = db.exec(
        select(NotificationPreference.user_id)
        .where(
            NotificationPreference.event_id == event_id,
            NotificationPreference.notification_type == notification_type,
            NotificationPreference.channel == channel,
            NotificationPreference.subscribed == True,
        )
        .distinct()
    ).all()

    logger.info(
        f"Found {len(subscribers)} subscribers for event {event_id}, "
        f"type {notification_type.value}, channel {channel.value}"
    )
    return list(subscribers)


def notify_event_updated(
    db: Session,
    *,
    event_id: int,
    event_changes: dict | None = None,
) -> None:
    """
    @brief Notify subscribers that an event has been updated.

    Gathers all subscribers for event_updated notifications.

    @param db Database session dependency.
    @param event_id ID of the event that was updated.
    @param event_changes Optional dictionary containing details about what changed.
    """
    from app.backend.event_service import get_event

    event = get_event(db=db, event_id=event_id)
    notification_data = {
        "event_name": event.name,
        "notification_type": NotificationType.event_updated.value,
        "changes": event_changes or {},
    }

    email_subscribers = get_notification_subscribers(
        db,
        event_id=event_id,
        notification_type=NotificationType.event_updated,
        channel=NotificationChannel.email,
    )

    if email_subscribers:
        emails = get_user_emails_by_ids(db, email_subscribers)
        logger.info(f"Sending event_updated email notifications to {len(emails)} users")
        send_email_notifications(emails, notification_data)


def notify_participant_joined(db: Session, *, event_id: int, new_participant_id: int) -> None:
    """
    @brief Notify subscribers that a new participant has joined the event.

    Gathers all subscribers for participant_joined notifications and calls the
    provided send_notification function for each channel separately.
    Users subscribed to both channels will receive notifications on both.

    @param db Database session dependency.
    @param event_id ID of the event.
    @param new_participant_id ID of the user who joined.
    """
    from app.backend.event_service import get_event

    event = get_event(db=db, event_id=event_id)
    new_participant = get_user(db=db, user_id=new_participant_id)
    notification_data = {
        "event_name": event.name,
        "notification_type": NotificationType.participant_joined.value,
        "new_participant_name": new_participant.login,
    }

    email_subscribers = get_notification_subscribers(
        db,
        event_id=event_id,
        notification_type=NotificationType.participant_joined,
        channel=NotificationChannel.email,
    )
    email_subscribers = [uid for uid in email_subscribers if uid != new_participant_id]

    if email_subscribers:
        emails = get_user_emails_by_ids(db, email_subscribers)
        logger.info(
            f"Sending participant_joined email notifications to {len(email_subscribers)} users"
        )
        send_email_notifications(emails, notification_data)
