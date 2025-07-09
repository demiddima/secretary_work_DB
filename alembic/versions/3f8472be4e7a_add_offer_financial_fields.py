"""add_offer_financial_fields

Revision ID: 3f8472be4e7a
Revises: 5e784061619f
Create Date: 2025-07-09 11:26:36.470219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f8472be4e7a'
down_revision: Union[str, Sequence[str], None] = '5e784061619f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('offers', sa.Column('payout', sa.Float(), nullable=False, server_default='0'))
    op.add_column('offers', sa.Column('to_you', sa.Float(), nullable=False, server_default='0'))
    op.add_column('offers', sa.Column('to_ludochat', sa.Float(), nullable=False, server_default='0'))
    op.add_column('offers', sa.Column('to_manager', sa.Float(), nullable=False, server_default='0'))
    op.add_column('offers', sa.Column('tax', sa.Float(), nullable=False, server_default='0'))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('offers', 'tax')
    op.drop_column('offers', 'to_manager')
    op.drop_column('offers', 'to_ludochat')
    op.drop_column('offers', 'to_you')
    op.drop_column('offers', 'payout')
