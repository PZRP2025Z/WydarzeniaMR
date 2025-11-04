"""
Database engine and session setup
"""

import logging
import os
from sqlmodel import create_engine, Session
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)

engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session
