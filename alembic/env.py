from logging.config import fileConfig
from contextlib import contextmanager

from sqlmodel import SQLModel
from sqlalchemy.orm import Session

from alembic import context
from app.database.models.comment import Comment
from app.database.models.event import Event
from app.database.models.event_invitation import EventInvitation
from app.database.models.event_pass import EventPass
from app.database.models.participations import EventParticipation
from app.database.models.user import User
from app.database.session import engine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_online():
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("Offline mode not supported. Use online mode.")
else:
    run_migrations_online()
