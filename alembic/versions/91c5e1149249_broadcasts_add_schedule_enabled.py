"""broadcasts: add schedule & enabled

Revision ID: 91c5e1149249
Revises: 8c0ea8c172ca
Create Date: 2025-08-26 19:41:01.550614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91c5e1149249'
down_revision: Union[str, Sequence[str], None] = '8c0ea8c172ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем строковое расписание (аналогично scheduled_announcements.schedule)
    op.add_column(
        "broadcasts",
        sa.Column("schedule", sa.String(length=255), nullable=True),
    )

    # Добавляем флаг активности; для существующих строк применится server_default
    # MySQL: BOOLEAN → TINYINT(1), server_default '1'
    op.add_column(
        "broadcasts",
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )

    # (опционально) если хочешь убрать server_default на уровне схемы после заполнения:
    # op.alter_column("broadcasts", "enabled", server_default=None)


def downgrade() -> None:
    op.drop_column("broadcasts", "enabled")
    op.drop_column("broadcasts", "schedule")
