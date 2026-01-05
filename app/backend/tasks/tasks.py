import os
import time
import dramatiq
from pydantic import EmailStr
from dramatiq.brokers.redis import RedisBroker
import logging
import dotenv
import smtplib
from email.message import EmailMessage

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
