"""Agregar last_saturation_date a fields (FAO-56 Sec 8.4.2)

Revision ID: b2c3d4e5f6a7
Revises: f1a2b3c4d5e6
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'fields',
        sa.Column('last_saturation_date', sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('fields', 'last_saturation_date')
