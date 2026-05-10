"""Expand SoilType enum a 12 clases FAO-56/USDA

Revision ID: f1a2b3c4d5e6
Revises: a1b2c3d4e5f6
Create Date: 2026-05-10
"""
from alembic import op

revision = 'f1a2b3c4d5e6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE soiltype RENAME TO soiltype_old")
    op.execute("""
        CREATE TYPE soiltype AS ENUM (
            'sand', 'loamy_sand', 'sandy_loam', 'sandy_clay_loam',
            'loam', 'silt_loam', 'silt',
            'clay_loam', 'silty_clay_loam',
            'sandy_clay', 'silty_clay', 'clay'
        )
    """)
    op.execute("""
        ALTER TABLE fields
        ALTER COLUMN soil_type TYPE soiltype
        USING CASE
            WHEN soil_type::text = 'sandy' THEN 'sandy_loam'::soiltype
            WHEN soil_type::text = 'loamy' THEN 'loam'::soiltype
            ELSE soil_type::text::soiltype
        END
    """)
    op.execute("DROP TYPE soiltype_old")


def downgrade() -> None:
    op.execute("ALTER TYPE soiltype RENAME TO soiltype_old")
    op.execute("CREATE TYPE soiltype AS ENUM ('sandy', 'loamy', 'clay')")
    op.execute("""
        ALTER TABLE fields
        ALTER COLUMN soil_type TYPE soiltype
        USING CASE
            WHEN soil_type::text IN ('sand', 'loamy_sand', 'sandy_loam', 'sandy_clay_loam') THEN 'sandy'::soiltype
            WHEN soil_type::text IN ('loam', 'silt_loam', 'silt', 'clay_loam', 'silty_clay_loam') THEN 'loamy'::soiltype
            ELSE 'clay'::soiltype
        END
    """)
    op.execute("DROP TYPE soiltype_old")
