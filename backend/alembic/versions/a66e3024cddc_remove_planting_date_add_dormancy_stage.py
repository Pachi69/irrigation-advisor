"""remove planting_date, add dormancy stage

Revision ID: a66e3024cddc
Revises: 06d3cef370d8
Create Date: 2026-05-19 17:24:01.974349

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a66e3024cddc'
down_revision: Union[str, None] = '06d3cef370d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Eliminar la columna planting_date de fields
    op.drop_column('fields', 'planting_date')
    # Agregar la etapa de reposo al enum phenologicalstage.
    # ADD VALUE debe correr fuera de la transaccion de la migracion.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE phenologicalstage ADD VALUE IF NOT EXISTS 'dormancy'")


def downgrade() -> None:
    # Restaurar la columna planting_date
    op.add_column('fields', sa.Column(
        'planting_date', sa.Date(), nullable=False,
        server_default=sa.text('CURRENT_DATE'),
    ))
    op.alter_column('fields', 'planting_date', server_default=None)
    # Quitar 'dormancy' del enum phenologicalstage recreando el tipo
    op.execute("ALTER TYPE phenologicalstage RENAME TO phenologicalstage_old")
    op.execute("CREATE TYPE phenologicalstage AS ENUM ('initial', 'development', 'mid', 'late')")
    op.execute(
        "ALTER TABLE daily_water_balances ALTER COLUMN phenological_stage "
        "TYPE phenologicalstage USING phenological_stage::text::phenologicalstage"
    )
    op.execute("DROP TYPE phenologicalstage_old")
