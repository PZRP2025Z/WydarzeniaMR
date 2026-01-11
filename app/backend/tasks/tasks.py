"""
<<<<<<< HEAD
@file tasks.py
@brief Handles sending emails asynchronously using Dramatiq and Redis.
=======
email_service.py
================

Handles sending emails asynchronously using Dramatiq and Redis.
>>>>>>> main

Provides functionality to send welcome emails to newly registered users.
Uses environment variables for email credentials and Redis broker configuration.
"""

import logging
import os
import smtplib
from email.message import EmailMessage

import dotenv
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from pydantic import EmailStr

from app.database.models.notifications import NotificationType
from app.database.models.user import UserEmailInfo

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_DB = os.getenv("REDIS_DB")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"


class TaskQueueError(Exception):
    """Raised when the task queue (Dramatiq/Redis) is unavailable."""

    pass


def send_welcome_email(to_email: EmailStr, user_name: str):
    """
    @brief  Queue sending a welcome email to a newly registered user.

    @param to_email Email address of the recipient.
    @param user_name Name of the recipient user.

    @raises TaskQueueError if unable to connect to a broker.

    This function constructs a simple welcome email and sends it using
    Gmail SMTP. The task is executed asynchronously via Dramatiq and Redis.
    """
    _send_welcome_email.send(to_email, user_name)


def send_email_notifications(
    user_emails: dict[int, UserEmailInfo],
    notification_data: dict,
) -> None:
    """
    @brief Queue email notifications for multiple users.

    @param user_emails Dictionary mapping user IDs to their email information.
    @param notification_data Dictionary containing notification details.

    Queues asynchronous email tasks for each recipient using Dramatiq.
    """
    for _, email_info in user_emails.items():
        _send_email_notification.send(email_info.email, email_info.login, notification_data)


dramatiq.set_broker(RedisBroker(url=redis_url))


@dramatiq.actor
def _send_welcome_email(to_email: EmailStr, user_name: str):
    """
    @brief Send a welcome email to a newly registered user.

    :param to_email: Email address of the recipient.
    :param user_name: Name of the recipient user.
    :return: None

    This function constructs a simple welcome email and sends it using
    Gmail SMTP. The task is executed asynchronously via Dramatiq and Redis.
    """
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = "Welcome to WydarzeniaMR!"

    text_body = (
        f"Hello {user_name},\n\n"
        "Welcome to WydarzeniaMR!\n\n"
        "We're excited to have you on board.\n\n"
        "Best regards,\n"
        "The WydarzeniaMR Team\n"
    )
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Hello {user_name},</h2>
                <p>Welcome to <strong>WydarzeniaMR</strong>!</p>
                <p>We're excited to have you on board.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #7f8c8d; font-size: 14px;">
                    Best regards,<br>
                    The WydarzeniaMR Team
                </p>
            </div>
        </body>
    </html>
    """

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    logging.info(f"Sending welcome email to {to_email}.")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Failed to send an email to {to_email}: {e}")


@dramatiq.actor
def _send_email_notification(to_email: str, user_name: str, notification_data: dict):
    """
    @brief Send an email notification to a user about event updates or new participants.

    @param to_email Email address of the recipient.
    @param user_name Name/login of the recipient user.
    @param notification_data Dictionary containing notification details.

    This function constructs and sends notification emails using Gmail SMTP.
    The task is executed asynchronously via Dramatiq and Redis.
    """
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    notification_type = notification_data.get("notification_type")
    event_name = notification_data.get("event_name")

    if notification_type == NotificationType.event_updated.value:
        msg["Subject"] = f"Event {event_name} has been updated"
        changes = notification_data.get("changes", {})
        changes_text = "\n".join([f"- {key}: {value}" for key, value in changes.items()])

        text_body = (
            f"Hello {user_name},\n\n"
            f"An event you're participating in has been updated.\n\n"
            f"Event: {event_name}\n"
            f"Changes:\n{changes_text if changes_text else 'Event details have been modified.'}\n\n"
            f"Best regards,\n"
            f"The WydarzeniaMR Team\n"
        )

        html_body = f"""
        <html>
            <body>
                <p>Hello {user_name},</p>
                <p>An event you're participating in has been updated.</p>
                <p><strong>Event: </strong> {event_name}</p>
                <p><strong>Changes:</strong></p>
                <ul>
                    {"".join([f"<li>{key}: {value}</li>" for key, value in changes.items()]) if changes else "<li>Event details have been modified.</li>"}
                </ul>
                <p>Best regards,<br>The WydarzeniaMR Team</p>
            </body>
        </html>
        """

    elif notification_type == NotificationType.participant_joined.value:
        new_participant_name = notification_data.get("new_participant_name")
        msg["Subject"] = f"New participant joined Event {event_name}"

        text_body = (
            f"Hello {user_name},\n\n"
            f"A new participant has joined an event you're part of.\n\n"
            f"Event: {event_name}\n"
            f"New Participant: {new_participant_name}\n\n"
            f"Best regards,\n"
            f"The WydarzeniaMR Team\n"
        )

        html_body = f"""
        <html>
            <body>
                <p>Hello {user_name},</p>
                <p>A new participant has joined an event you're part of.</p>
                <p><strong>Event:</strong>{event_name}</p>
                <p><strong>New Participant:</strong> {new_participant_name}</p>
                <p>Best regards,<br>The WydarzeniaMR Team</p>
            </body>
        </html>
        """
    else:
        logger.error(f"Unknown notification type: {notification_type}")
        return

    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    logger.info(f"Sending {notification_type} notification to {to_email}")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        logger.error(f"Failed to send notification email to {to_email}: {e}")
