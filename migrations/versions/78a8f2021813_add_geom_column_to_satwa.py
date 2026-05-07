"""add geom column to satwa

Revision ID: 78a8f2021813
Revises: cb39019369ab
Create Date: 2026-01-20 14:26:07.896855

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

# revision identifiers, used by Alembic.
revision: str = '78a8f2021813'
down_revision: Union[str, Sequence[str], None] = 'cb39019369ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Tambah kolom geom ke tabel satwa
    op.add_column('satwa', sa.Column('geom', Geometry(geometry_type='POINT', srid=4326)))


def downgrade() -> None:
    """Downgrade schema."""
    # Hapus kolom geom kalau rollback
    op.drop_column('satwa', 'geom')