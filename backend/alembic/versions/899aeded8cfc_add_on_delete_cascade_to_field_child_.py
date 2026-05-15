"""add on delete cascade to field child fkeys

Revision ID: 899aeded8cfc
Revises: 418715b7d7b4
Create Date: 2026-05-15 11:39:57.037332

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '899aeded8cfc'
down_revision: Union[str, None] = '418715b7d7b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('satellite_records_field_id_fkey', 'satellite_records', type_='foreignkey')
    op.create_foreign_key(
        'satellite_records_field_id_fkey', 'satellite_records', 'fields',
        ['field_id'], ['id'], ondelete='CASCADE',
    )

    op.drop_constraint('alerts_field_id_fkey', 'alerts', type_='foreignkey')
    op.create_foreign_key(
        'alerts_field_id_fkey', 'alerts', 'fields',
        ['field_id'], ['id'], ondelete='CASCADE',
    )

    op.drop_constraint('irrigation_confirmations_field_id_fkey', 'irrigation_confirmations', type_='foreignkey')
    op.create_foreign_key(
        'irrigation_confirmations_field_id_fkey', 'irrigation_confirmations', 'fields',
        ['field_id'], ['id'], ondelete='CASCADE',
    )

    op.drop_constraint('irrigation_confirmations_recommendation_id_fkey', 'irrigation_confirmations', type_='foreignkey')
    op.create_foreign_key(
        'irrigation_confirmations_recommendation_id_fkey', 'irrigation_confirmations', 'recommendations',
        ['recommendation_id'], ['id'], ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('irrigation_confirmations_recommendation_id_fkey', 'irrigation_confirmations', type_='foreignkey')
    op.create_foreign_key(
        'irrigation_confirmations_recommendation_id_fkey', 'irrigation_confirmations', 'recommendations',
        ['recommendation_id'], ['id'],
    )

    op.drop_constraint('irrigation_confirmations_field_id_fkey', 'irrigation_confirmations', type_='foreignkey')
    op.create_foreign_key(
        'irrigation_confirmations_field_id_fkey', 'irrigation_confirmations', 'fields',
        ['field_id'], ['id'],
    )

    op.drop_constraint('alerts_field_id_fkey', 'alerts', type_='foreignkey')
    op.create_foreign_key(
        'alerts_field_id_fkey', 'alerts', 'fields',
        ['field_id'], ['id'],
    )

    op.drop_constraint('satellite_records_field_id_fkey', 'satellite_records', type_='foreignkey')
    op.create_foreign_key(
        'satellite_records_field_id_fkey', 'satellite_records', 'fields',
        ['field_id'], ['id'],
    )
