"""add last_message_id to scheduled_announcements

Revision ID: a1b2c3d4e5f6
Revises: 24739d1b7538
Create Date: 2025-08-13 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '24739d1b7538'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        'scheduled_announcements',
        sa.Column('last_message_id', sa.Integer(), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('scheduled_announcements', 'last_message_id')
