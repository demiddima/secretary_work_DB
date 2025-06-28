"""add terms_accepted to users

Revision ID: 577731173810
Revises: ebcff93260a4
Create Date: 2025-06-29 08:45:44.439481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '577731173810'
down_revision: Union[str, Sequence[str], None] = 'ebcff93260a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('users', sa.Column('terms_accepted', sa.Boolean(), nullable=False, server_default=sa.text('0')))

def downgrade():
    op.drop_column('users', 'terms_accepted')

