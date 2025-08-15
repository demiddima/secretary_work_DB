"""rename cron->schedule and add next_announcements

Revision ID: 7a2c4d9f1b23
Revises: a1b2c3d4e5f6
Create Date: 2025-08-15 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a2c4d9f1b23'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем новый столбец
    op.add_column(
        'scheduled_announcements',
        sa.Column('next_announcements', sa.DateTime(), nullable=True)
    )
    # Переименовываем cron -> schedule
    op.alter_column(
        'scheduled_announcements',
        'cron',
        new_column_name='schedule',
        existing_type=sa.String(length=255),
        existing_nullable=False
    )


def downgrade() -> None:
    # Переименовываем обратно schedule -> cron
    op.alter_column(
        'scheduled_announcements',
        'schedule',
        new_column_name='cron',
        existing_type=sa.String(length=255),
        existing_nullable=False
    )
    # Удаляем столбец next_announcements
    op.drop_column('scheduled_announcements', 'next_announcements')
