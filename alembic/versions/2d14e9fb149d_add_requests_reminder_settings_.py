"""add_requests_reminder_settings_notifications_tables

Revision ID: 2d14e9fb149d
Revises: 60dd695a22f9
Create Date: 2025-07-08 16:43:31.275237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d14e9fb149d'
down_revision: Union[str, Sequence[str], None] = '60dd695a22f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Таблица requests
    op.create_table(
        'requests',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('offer_name', sa.String(length=64), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('ix_requests_user_id', 'requests', ['user_id'])

    # 2) Таблица reminder_settings
    op.create_table(
        'reminder_settings',
        sa.Column('request_id', sa.Integer(), primary_key=True),
        sa.Column('first_notification_at', sa.DateTime(), nullable=False),
        sa.Column('frequency_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # 3) Таблица notifications
    op.create_table(
        'notifications',
        sa.Column('request_id', sa.Integer(), primary_key=True),
        sa.Column('notification_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('notifications')
    op.drop_table('reminder_settings')
    op.drop_index('ix_requests_user_id', table_name='requests')
    op.drop_table('requests')
