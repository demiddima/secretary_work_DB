"""Rename invite_links, add links table

Revision ID: ada14aadae04
Revises: d9f2ef3cbb8b
Create Date: 2025-06-21 16:43:50.288479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'ada14aadae04'
down_revision: Union[str, Sequence[str], None] = 'd9f2ef3cbb8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # переименование старой таблицы
    op.rename_table('invite_links', 'invite_links_chats')
    # создание новой таблицы links
    op.create_table(
        'links',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('link_key', sa.String(length=512), nullable=False, unique=True),
        sa.Column('visits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

def downgrade():
    # в откате — удалить новую таблицу и вернуть старое имя
    op.drop_table('links')
    op.rename_table('invite_links_chats', 'invite_links')
    
    



