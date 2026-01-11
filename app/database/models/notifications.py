"""
@file notifications.py
@brief Database models for notification preferences and tracking.

Provides SQLModel and Pydantic models for managing user notification
preferences for events, including email.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class NotificationType(str, Enum):
    """
    @brief Enum representing types of notifications.

    Options:
    - event_updated: owner changed event details
    - participant_joined: someone joined the event
    """

    event_updated = "event_updated"
    participant_joined = "participant_joined"


class NotificationChannel(str, Enum):
    """
    @brief Enum representing notification delivery channels.

    Options:
    - email: send via email
    """

    email = "email"


class NotificationPreference(SQLModel, table=True):
    """
    @brief Database table model for user notification preferences per event.

    Tracks which notification types and channels a user has subscribed to for a specific event.

    @param id Primary key of the notification preference record.
    @param user_id ID of the user.
    @param event_id ID of the event.
    @param notification_type Type of notification (event_updated, participant_joined).
    @param channel Delivery channel (email).
    @param subscribed Whether the user is subscribed to this notification.
    @param created_at Timestamp when preference was created.
    """

    __tablename__ = "notification_preferences"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    event_id: int = Field(foreign_key="events.id", index=True)
    notification_type: NotificationType
    channel: NotificationChannel
    subscribed: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationPreferenceCreate(BaseModel):
    """
    @brief Pydantic model for creating/updating a notification preference.

    @param notification_type Type of notification to subscribe to.
    @param channel Delivery channel for the notification.
    @param subscribed Whether to subscribe (True) or unsubscribe (False).
    """

    notification_type: NotificationType
    channel: NotificationChannel
    subscribed: bool = True


class NotificationPreferenceUpdate(BaseModel):
    """
    @brief Pydantic model for bulk updating notification preferences.

    @param preferences List of notification preferences to update.
    """

    preferences: list[NotificationPreferenceCreate]
