"""initial schema

Revision ID: c693a40b83a5
Revises: 658f61c797a4
Create Date: 2026-01-11 14:27:11.229140

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c693a40b83a5'
down_revision: Union[str, Sequence[str], None] = '658f61c797a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
