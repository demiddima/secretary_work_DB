"""broadcasts: drop scheduled_at (leave schedule+enabled)

Revision ID: 3c0532540e20
Revises: 91c5e1149249
Create Date: 2025-08-26 20:36:51.099842

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c0532540e20'
down_revision: Union[str, Sequence[str], None] = '91c5e1149249'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Безопасно дропаем индекс, если он существует
    bind = op.get_bind()
    insp = sa.inspect(bind)
    idx_names = {ix["name"] for ix in insp.get_indexes("broadcasts")}
    if "ix_broadcasts_scheduled_at" in idx_names:
        op.drop_index("ix_broadcasts_scheduled_at", table_name="broadcasts")

    # Дроп самой колонки
    with op.batch_alter_table("broadcasts") as batch_op:
        batch_op.drop_column("scheduled_at")


def downgrade() -> None:
    # Вернём колонку обратно (naive DATETIME), без TZ
    with op.batch_alter_table("broadcasts") as batch_op:
        batch_op.add_column(sa.Column("scheduled_at", sa.DateTime(timezone=False), nullable=True))

    # Восстановим индекс для совместимости со старым кодом
    op.create_index(
        "ix_broadcasts_scheduled_at",
        "broadcasts",
        ["scheduled_at"],
        unique=False,
    )
