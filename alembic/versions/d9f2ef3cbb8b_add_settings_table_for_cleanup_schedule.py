"""add settings table for cleanup schedule

Revision ID: d9f2ef3cbb8b
Revises: 04bd54e3d701
Create Date: 2025-06-18 10:31:40.265541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9f2ef3cbb8b'
down_revision: Union[str, Sequence[str], None] = '04bd54e3d701'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'settings',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('cleanup_cron', sa.String(100), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
    )
    op.execute(
        "INSERT INTO settings (id, cleanup_cron) VALUES (1, '0 3 * * 6')"
    )

def downgrade():
    op.drop_table('settings')
