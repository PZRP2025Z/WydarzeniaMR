"""
@file session.py
@brief Database engine and session setup.

Sets up the SQLModel/SQLAlchemy engine and provides a session generator
for dependency injection in FastAPI routes and backend services.
"""

import logging
import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL
from sqlmodel import Session, create_engine

load_dotenv()
DB_USER = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_DRIVER_NAME = os.getenv("DB_DRIVER_NAME")

logger = logging.getLogger(__name__)

DATABASE_URL = URL.create(
    drivername=DB_DRIVER_NAME,
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)

engine = create_engine(DATABASE_URL)


def get_session():
    """
    @brief SQLModel session generator.

    Yields a database session for use in FastAPI dependencies or
    backend services. Ensures that the session is properly closed
    after usage.

    @return Yields a SQLModel Session object.
    """
    with Session(engine) as session:
        yield session
