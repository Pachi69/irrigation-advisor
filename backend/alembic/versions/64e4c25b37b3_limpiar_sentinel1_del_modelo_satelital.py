"""limpiar sentinel1 del modelo satelital

Revision ID: 64e4c25b37b3
Revises: d53c1526a614
Create Date: 2026-05-27 18:10:29.986853

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64e4c25b37b3'
down_revision: Union[str, None] = 'd53c1526a614'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.drop_column('satellite_records', 'moisture_event_detected')
    op.drop_column('satellite_records', 'backscatter_vh')
    op.drop_column('satellite_records', 'backscatter_vv')
    op.drop_column('satellite_records', 'source')
    op.execute("DROP TYPE IF EXISTS satellitesource")


def downgrade():
    op.execute("CREATE TYPE satellitesource AS ENUM ('sentinel2', 'sentinel1')")
    op.execute(
        "ALTER TABLE satellite_records ADD COLUMN source satellitesource NOT NULL DEFAULT 'sentinel2'"
    )
    op.add_column('satellite_records', sa.Column('backscatter_vv', sa.Float(), nullable=True))
    op.add_column('satellite_records', sa.Column('backscatter_vh', sa.Float(), nullable=True))
    op.add_column('satellite_records', sa.Column('moisture_event_detected', sa.Boolean(), nullable=True, server_default='false'))