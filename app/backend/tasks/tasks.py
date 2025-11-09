import os
import time
import dramatiq
from pydantic import EmailStr
from dramatiq.brokers.redis import RedisBroker
import logging
import dotenv

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_DB = os.getenv("REDIS_DB")

redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

redis_broker = RedisBroker(url=redis_url)
dramatiq.set_broker(redis_broker)


@dramatiq.actor
def send_welcome_email(to_email: EmailStr, user_name: str):
    subject = "Welcome to WydarzeniaMR!"
    body = f"Hello {user_name},\n\nThanks for joining!"
    logging.info(f'Sending email to {to_email}. Subject: "{subject}". Body: "{body}"')
    time.sleep(2)
