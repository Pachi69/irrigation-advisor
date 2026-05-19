"""remove alfalfa and irrigation_type

Revision ID: 06d3cef370d8
Revises: 899aeded8cfc
Create Date: 2026-05-19 11:40:04.505144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06d3cef370d8'
down_revision: Union[str, None] = '899aeded8cfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Eliminar la columna irrigation_type
    op.drop_column('fields', 'irrigation_type')
    # 2. Eliminar el tipo enum irrigationtype (ya sin uso)
    op.execute("DROP TYPE irrigationtype")
    # 3. Recrear croptype sin 'alfalfa'
    #    (requiere que ninguna fila use crop_type='alfalfa')
    op.execute("ALTER TYPE croptype RENAME TO croptype_old")
    op.execute("CREATE TYPE croptype AS ENUM ('vine', 'peach')")
    op.execute(
        "ALTER TABLE fields ALTER COLUMN crop_type "
        "TYPE croptype USING crop_type::text::croptype"
    )
    op.execute("DROP TYPE croptype_old")


def downgrade() -> None:
    # Revertir croptype: volver a agregar 'alfalfa'
    op.execute("ALTER TYPE croptype RENAME TO croptype_old")
    op.execute("CREATE TYPE croptype AS ENUM ('vine', 'peach', 'alfalfa')")
    op.execute(
        "ALTER TABLE fields ALTER COLUMN crop_type "
        "TYPE croptype USING crop_type::text::croptype"
    )
    op.execute("DROP TYPE croptype_old")
    # Recrear la columna irrigation_type (sa.Enum recrea el tipo)
    op.add_column('fields', sa.Column(
        'irrigation_type',
        sa.Enum('drip', 'sprinkler', 'flood', name='irrigationtype'),
        nullable=False,
        server_default='drip',
    ))
    op.alter_column('fields', 'irrigation_type', server_default=None)
