"""rename cleanup_cron to value in settings_2

Revision ID: d886fca72669
Revises: 6d7db4b3a9d5
Create Date: 2025-07-08 10:50:24.277507
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd886fca72669'
down_revision: Union[str, Sequence[str], None] = '6d7db4b3a9d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'settings',
        'cleanup_cron',
        new_column_name='value',
        type_=sa.String(100),
        existing_type=sa.String(100),
        existing_nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        'settings',
        'value',
        new_column_name='cleanup_cron',
        type_=sa.String(100),
        existing_type=sa.String(100),
        existing_nullable=False
    )
