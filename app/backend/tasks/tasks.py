"""
@file email_service.py
@brief Handles sending emails asynchronously using Dramatiq and Redis.

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

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_DB = os.getenv("REDIS_DB")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

redis_broker = RedisBroker(url=redis_url)
dramatiq.set_broker(redis_broker)


@dramatiq.actor
def send_welcome_email(to_email: EmailStr, user_name: str):
    """
    @brief Send a welcome email to a newly registered user.

    @param to_email Email address of the recipient.
    @param user_name Name of the recipient user.

    This function constructs a simple welcome email and sends it using
    Gmail SMTP. The task is executed asynchronously via Dramatiq and Redis.
    """
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = "Welcome to WydarzeniaMR!"
    body = f"Hello {user_name},\n\nThanks for joining!"
    msg.set_content(body)
    logging.info(f"Sending welcome email to {to_email}.")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)
