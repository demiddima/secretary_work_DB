"""rename cleanup_cron to value in settings

Revision ID: 6d7db4b3a9d5
Revises: 577731173810
Create Date: 2025-07-08 10:44:07.662275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d7db4b3a9d5'
down_revision: Union[str, Sequence[str], None] = '577731173810'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('settings', 'cleanup_cron', new_column_name='value')


def downgrade() -> None:
    op.alter_column('settings', 'value', new_column_name='cleanup_cron')
