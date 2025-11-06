import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from app.routes import event_routes
from .logger import setup_logging
from .database.session import engine

app = FastAPI()

logger = logging.getLogger(__name__)
setup_logging()

logger.info("Starting Application")
app = FastAPI(title="WydarzeniaMR_API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],  # adres frontendu Svelte
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],
)

SQLModel.metadata.create_all(engine)
app.include_router(event_routes.router)
