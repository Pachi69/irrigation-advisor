"""drop_ndwi_evi_from_satellite_records

Revision ID: 33a4c8c2df03
Revises: 9e224f5d6a35
Create Date: 2026-04-29 22:46:25.936264

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33a4c8c2df03'
down_revision: Union[str, None] = '9e224f5d6a35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('satellite_records', 'ndwi')
    op.drop_column('satellite_records', 'evi')


def downgrade() -> None:
    op.add_column('satellite_records', sa.Column('ndwi', sa.Float(), nullable=True))
    op.add_column('satellite_records', sa.Column('evi', sa.Float(), nullable=True))
