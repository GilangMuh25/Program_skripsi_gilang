"""add satwa_gambar

Revision ID: f1084c940d06
Revises: 467ef7434719
Create Date: 2026-04-04 16:01:25.348665

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f1084c940d06'
down_revision: Union[str, Sequence[str], None] = '467ef7434719'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    """op.create_table(
        'satwa_gambar',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('satwa_id', sa.Integer, sa.ForeignKey('satwa.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(200), nullable=False)
    )"""


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('satwa_gambar')