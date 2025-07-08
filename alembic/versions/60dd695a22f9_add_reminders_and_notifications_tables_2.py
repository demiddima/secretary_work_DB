"""add reminders and notifications tables_2

Revision ID: 60dd695a22f9
Revises: 6fa45da1f08f
Create Date: 2025-07-08 12:02:53.519129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60dd695a22f9'
down_revision: Union[str, Sequence[str], None] = '6fa45da1f08f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём таблицу reminders
    op.create_table(
        'reminders',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('internal_user_id', sa.BigInteger(), nullable=False),
        sa.Column('internal_request_id', sa.String(36), nullable=False),
        sa.Column('first_notification_at', sa.DateTime(), nullable=False),
        sa.Column('frequency_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('offer_name', sa.Text(), nullable=False),
        sa.Column('is_offer_completed', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('offer_payout', sa.String(255), nullable=True),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    # Индекс для FK
    op.create_index(
        'idx_reminders_internal_request_id',
        'reminders',
        ['internal_request_id']
    )

    # Создаём таблицу notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('internal_request_id', sa.String(36), nullable=False),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ['internal_request_id'],
            ['reminders.internal_request_id'],
            ondelete='CASCADE'
        ),
        sa.Index('idx_notifications_request', 'internal_request_id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_index('idx_reminders_internal_request_id', table_name='reminders')
    op.drop_table('reminders')
