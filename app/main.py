import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.routes import event_routes
from app.routes import auth_routes
from app.routes import user_routes
from app.routes import comment_routes

from app.logger import setup_logging
from app.database.session import engine

logger = logging.getLogger(__name__)
setup_logging()
logger.info("Starting Application")


def init_db():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down application")


app = FastAPI(title="WydarzeniaMR_API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(event_routes.router)
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(comment_routes.router)
