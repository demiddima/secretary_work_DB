"""fix next_announcements zero dates

Revision ID: 8ab15147f4c0
Revises: 7a2c4d9f1b23
Create Date: 2025-08-15 15:05:42.877921

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ab15147f4c0'
down_revision: Union[str, Sequence[str], None] = '7a2c4d9f1b23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Почистить мусорные значения в уже существующих строках
    op.execute("""
        UPDATE scheduled_announcements
        SET next_announcements = NULL
        WHERE next_announcements = '0000-00-00 00:00:00'
           OR next_announcements = '0000-00-00';
    """)

    # 2) Убедиться, что колонка допускает NULL и не имеет дефолта-нуля
    op.alter_column(
        'scheduled_announcements',
        'next_announcements',
        existing_type=sa.DateTime(),
        nullable=True,
        server_default=None
    )

def downgrade() -> None:
    # Откат только структуры (данные уже очищены)
    op.alter_column(
        'scheduled_announcements',
        'next_announcements',
        existing_type=sa.DateTime(),
        nullable=True
    )