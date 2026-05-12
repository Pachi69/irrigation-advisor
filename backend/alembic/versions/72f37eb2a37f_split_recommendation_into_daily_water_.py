"""split_recommendation_into_daily_water_balance

Revision ID: 72f37eb2a37f
Revises: d7dcfd0fb018
Create Date: 2026-05-12 11:20:15.988144

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

# revision identifiers, used by Alembic.
revision: str = '72f37eb2a37f'
down_revision: Union[str, None] = 'd7dcfd0fb018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tipos enum existentes en PostgreSQL — no recrear
    kcsource = PgEnum('s2_dynamic', 'tabular', name='kcsource', create_type=False)
    phenologicalstage = PgEnum('initial', 'development', 'mid', 'late', name='phenologicalstage', create_type=False)
    urgencylevel = PgEnum('low', 'medium', 'high', 'critical', name='urgencylevel', create_type=False)
    confidencelevel = PgEnum('low', 'medium', 'high', name='confidencelevel', create_type=False)

    # Eliminar FK de irrigation_confirmations → recommendations antes de dropear la tabla
    op.drop_constraint(
        'irrigation_confirmations_recommendation_id_fkey',
        'irrigation_confirmations',
        type_='foreignkey',
    )
    op.drop_table('recommendations')

    # Crear tabla daily_water_balances
    op.create_table(
        'daily_water_balances',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('eto_mm', sa.Float(), nullable=False),
        sa.Column('kc', sa.Float(), nullable=False),
        sa.Column('kc_source', kcsource, nullable=False),
        sa.Column('etc_mm', sa.Float(), nullable=False),
        sa.Column('water_deficit_mm', sa.Float(), nullable=False),
        sa.Column('ks', sa.Float(), nullable=False),
        sa.Column('phenological_stage', phenologicalstage, nullable=False),
        sa.Column('precipitation_mm', sa.Float(), nullable=False),
        sa.Column('taw_mm', sa.Float(), nullable=False),
        sa.Column('raw_mm', sa.Float(), nullable=True),
        sa.Column('ndvi', sa.Float(), nullable=True),
        sa.Column('ndvi_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['field_id'], ['fields.id'], name='daily_water_balances_field_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='daily_water_balances_pkey'),
        sa.UniqueConstraint('field_id', 'date', name='uq_balance_field_date'),
    )
    op.create_index('ix_daily_water_balances_field_id', 'daily_water_balances', ['field_id'])

    # Crear nueva tabla recommendations (solo la decision)
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('water_balance_id', sa.Integer(), nullable=False),
        sa.Column('recommended_irrigation_mm', sa.Float(), nullable=False),
        sa.Column('urgency', urgencylevel, nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('confidence', confidencelevel, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['water_balance_id'], ['daily_water_balances.id'], name='recommendations_water_balance_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='recommendations_pkey'),
        sa.UniqueConstraint('water_balance_id', name='uq_recommendation_water_balance'),
    )
    op.create_index('ix_recommendations_water_balance_id', 'recommendations', ['water_balance_id'], unique=True)

    # Restaurar FK de irrigation_confirmations → nueva tabla recommendations
    op.create_foreign_key(
        'irrigation_confirmations_recommendation_id_fkey',
        'irrigation_confirmations', 'recommendations',
        ['recommendation_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('irrigation_confirmations_recommendation_id_fkey', 'irrigation_confirmations', type_='foreignkey')
    op.drop_table('recommendations')
    op.drop_table('daily_water_balances')

    # Recrear tabla recommendations original
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('eto_mm', sa.Float(), nullable=False),
        sa.Column('kc', sa.Float(), nullable=False),
        sa.Column('kc_source', sa.Enum('s2_dynamic', 'tabular', name='kcsource', create_type=False), nullable=False),
        sa.Column('etc_mm', sa.Float(), nullable=False),
        sa.Column('water_deficit_mm', sa.Float(), nullable=False),
        sa.Column('ks', sa.Float(), nullable=False),
        sa.Column('phenological_stage', sa.Enum('initial', 'development', 'mid', 'late', name='phenologicalstage', create_type=False), nullable=False),
        sa.Column('recommended_irrigation_mm', sa.Float(), nullable=False),
        sa.Column('urgency', sa.Enum('low', 'medium', 'high', 'critical', name='urgencylevel', create_type=False), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('precipitation_mm', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Enum('low', 'medium', 'high', name='confidencelevel', create_type=False), nullable=False),
        sa.Column('taw_mm', sa.Float(), nullable=True),
        sa.Column('raw_mm', sa.Float(), nullable=True),
        sa.Column('ndvi', sa.Float(), nullable=True),
        sa.Column('ndvi_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['field_id'], ['fields.id'], name='recommendations_field_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='recommendations_pkey'),
    )
    op.create_index('ix_recommendations_field_id', 'recommendations', ['field_id'])
    op.create_foreign_key(
        'irrigation_confirmations_recommendation_id_fkey',
        'irrigation_confirmations', 'recommendations',
        ['recommendation_id'], ['id'],
    )
