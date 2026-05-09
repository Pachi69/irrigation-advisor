"""add thumbnail_png to satellite_records

Revision ID: a1b2c3d4e5f6
Revises: 33a4c8c2df03
Create Date: 2026-05-09
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '33a4c8c2df03'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'satellite_records',
        sa.Column('thumbnail_png', sa.LargeBinary(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('satellite_records', 'thumbnail_png')
