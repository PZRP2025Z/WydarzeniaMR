import logging

from fastapi import FastAPI
from sqlmodel import SQLModel
from app.routes import event_routes
from .logger import setup_logging
from .database.session import engine


logger = logging.getLogger(__name__)
setup_logging()

logger.info("Starting Application")
app = FastAPI(title="WydarzeniaMR_API")

SQLModel.metadata.create_all(engine)
app.include_router(event_routes.router)
