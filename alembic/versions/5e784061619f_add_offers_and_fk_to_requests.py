"""add_offers_and_fk_to_requests

Revision ID: 5e784061619f
Revises: 2d14e9fb149d
Create Date: 2025-07-09 11:16:45.634456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e784061619f'
down_revision: Union[str, Sequence[str], None] = '2d14e9fb149d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создаём таблицу offers
    op.create_table(
        'offers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('income', sa.Float(), nullable=False),
        sa.Column('expense', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # Добавляем offer_id в requests
    op.add_column('requests', sa.Column('offer_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_requests_offer_id', 'requests', 'offers', ['offer_id'], ['id'], ondelete='CASCADE'
    )

    # Удаляем offer_name
    op.drop_column('requests', 'offer_name')


def downgrade() -> None:
    """Downgrade schema."""
    # Добавляем offer_name обратно
    op.add_column('requests', sa.Column('offer_name', sa.String(length=64), nullable=False))

    # Удаляем внешний ключ и offer_id
    op.drop_constraint('fk_requests_offer_id', 'requests', type_='foreignkey')
    op.drop_column('requests', 'offer_id')

    # Удаляем таблицу offers
    op.drop_table('offers')
