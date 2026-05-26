"""achicar alerttype a frost y heat_wave

Revision ID: e9cf5a63e80b
Revises: a66e3024cddc
Create Date: 2026-05-26 11:07:05.334962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9cf5a63e80b'
down_revision: Union[str, None] = 'a66e3024cddc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Por las dudas: no deberian existir alertas con los tipos a eliminar
    op.execute("DELETE FROM alerts WHERE type IN ('hail', 'critical_deficit')")
    op.execute("ALTER TYPE alerttype RENAME TO alerttype_old")
    op.execute("CREATE TYPE alerttype AS ENUM ('frost', 'heat_wave')")
    op.execute("ALTER TABLE alerts ALTER COLUMN type TYPE alerttype USING type::text::alerttype")
    op.execute("DROP TYPE alerttype_old")


def downgrade() -> None:
    op.execute("ALTER TYPE alerttype RENAME TO alerttype_old")
    op.execute("CREATE TYPE alerttype AS ENUM ('frost', 'hail', 'heat_wave', 'critical_deficit')")
    op.execute("ALTER TABLE alerts ALTER COLUMN type TYPE alerttype USING type::text::alerttype")
    op.execute("DROP TYPE alerttype_old")
