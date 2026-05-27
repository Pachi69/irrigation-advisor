"""snapshot estado hidrico en recomendacion (inmutable)

Revision ID: d53c1526a614
Revises: e9cf5a63e80b
Create Date: 2026-05-27 17:08:59.297236

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd53c1526a614'
down_revision: Union[str, None] = 'e9cf5a63e80b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('recommendations', sa.Column('water_deficit_mm', sa.Float(), nullable=True))
    op.add_column('recommendations', sa.Column('ks', sa.Float(), nullable=True))
    op.add_column('recommendations', sa.Column('taw_mm', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('recommendations', 'taw_mm')
    op.drop_column('recommendations', 'ks')
    op.drop_column('recommendations', 'water_deficit_mm')
