"""
@file main.py
@brief FastAPI application entrypoint.

Sets up the API application, including:
- Middleware setup (CORS).
- Inclusion of all API routers for events, authentication, users, comments, passes, and participations.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import event_routes
from app.routes import auth_routes
from app.routes import user_routes
from app.routes import comment_routes
from app.routes import passes_routes
from app.routes import participations_routes
from app.routes import invites_routes

from app.logger import setup_logging

logger = logging.getLogger(__name__)
setup_logging()
logger.info("Starting Application")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application started")
    yield
    logger.info("Shutting down application")


app = FastAPI(title="WydarzeniaMR_API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
