"""add_total_sup_offers

Revision ID: 241244847855
Revises: 61f2444764c8
Create Date: 2025-07-09 15:49:24.867859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '241244847855'
down_revision: Union[str, Sequence[str], None] = '61f2444764c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Добавляем поле total_sum в таблицу offers
    op.add_column('offers', sa.Column('total_sum', sa.Float(), nullable=False))
    

def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем столбец total_sum в случае отката миграции
    op.drop_column('offers', 'total_sum')
