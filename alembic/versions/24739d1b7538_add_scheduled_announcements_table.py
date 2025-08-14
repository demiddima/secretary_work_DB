"""add scheduled_announcements table

Revision ID: 24739d1b7538
Revises: e2fb640b3e45
Create Date: 2025-08-07 10:22:05.902255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24739d1b7538'
down_revision: Union[str, Sequence[str], None] = 'e2fb640b3e45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'scheduled_announcements',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('cron', sa.String(length=255), nullable=False),
    )

def downgrade():
    op.drop_table('scheduled_announcements')
