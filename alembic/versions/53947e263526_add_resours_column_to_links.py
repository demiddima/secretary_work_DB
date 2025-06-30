"""Add resours column to links

Revision ID: 53947e263526
Revises: ada14aadae04
Create Date: 2025-06-21 17:32:32.983237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53947e263526'
down_revision: Union[str, Sequence[str], None] = 'ada14aadae04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # убираем старое уникальное ограничение, если оно осталось после переименования
    op.drop_constraint('uq_invite_user_chat', 'invite_links_chats', type_='unique')
    # создаём уникальное ограничение заново
    op.create_unique_constraint(
        'uq_invite_user_chat',
        'invite_links_chats',
        ['user_id', 'chat_id']
    )
    # добавляем колонку resours
    op.add_column('links', sa.Column('resours', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # удаляем колонку resours
    op.drop_column('links', 'resours')
    # удаляем уникальное ограничение
    op.drop_constraint('uq_invite_user_chat', 'invite_links_chats', type_='unique')
