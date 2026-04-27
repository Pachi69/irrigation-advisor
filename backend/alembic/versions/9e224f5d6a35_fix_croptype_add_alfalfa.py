"""fix_croptype_add_alfalfa

Revision ID: 9e224f5d6a35
Revises: b7a7d032f86e
Create Date: 2026-04-27 19:45:09.193130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e224f5d6a35'
down_revision: Union[str, None] = 'b7a7d032f86e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE croptype ADD VALUE IF NOT EXISTS 'alfalfa'")


def downgrade() -> None:
    pass
