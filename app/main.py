"""
@file main.py
@brief FastAPI application entrypoint.

Sets up the API application, including:
- Database initialization with retry logic.
- Lifespan context for startup and shutdown logging.
- Middleware setup (CORS).
- Inclusion of all API routers for events, authentication, users, comments, passes, and participations.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from sqlalchemy.exc import OperationalError

from app.routes import event_routes
from app.routes import auth_routes
from app.routes import user_routes
from app.routes import comment_routes
from app.routes import passes_routes
from app.routes import participations_routes
from app.routes import invites_routes

from app.logger import setup_logging
from app.database.session import engine

logger = logging.getLogger(__name__)
setup_logging()
logger.info("Starting Application")


def init_db(retries: int = 30, delay: float = 1.0):
    """
    @brief Initialize the database schema.

    Drops all existing tables and recreates them.
    Retries the connection in case the database is not ready.

    @param retries Number of attempts to connect before failing.
    @param delay Delay in seconds between retries.

    @raises RuntimeError if unable to connect after all retries.
    """
    for attempt in range(1, retries + 1):
        try:
            SQLModel.metadata.drop_all(engine)
            SQLModel.metadata.create_all(engine)
            logger.info("Database initialized successfully")
            return
        except OperationalError as e:
            logger.warning(f"Database not ready, retry {attempt}/{retries}: {e}")
            time.sleep(delay)
    logger.error(f"Could not connect to database after {retries} attempts")
    raise RuntimeError("Database not ready")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    @brief FastAPI lifespan context.

    Handles startup and shutdown events:
    - Initializes the database on startup.
    - Logs shutdown message on exit.

    @yield None
    """
    init_db()
    yield
    logger.info("Shutting down application")


app = FastAPI(title="WydarzeniaMR_API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set exact frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(event_routes.router)
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(comment_routes.router)
app.include_router(passes_routes.router)
app.include_router(participations_routes.router)
app.include_router(invites_routes.router)
