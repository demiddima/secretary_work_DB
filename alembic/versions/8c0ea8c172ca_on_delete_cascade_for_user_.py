"""ON DELETE CASCADE for user_subscriptions.user_id

Revision ID: 8c0ea8c172ca
Revises: d471b1265bc8
Create Date: 2025-08-23 20:33:26.805455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c0ea8c172ca'
down_revision: Union[str, Sequence[str], None] = 'd471b1265bc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    # 1) Чистим сиротские строки, иначе добавление FK может упасть
    bind.execute(sa.text("""
        DELETE us
        FROM user_subscriptions us
        LEFT JOIN users u ON u.id = us.user_id
        WHERE u.id IS NULL
    """))

    # 2) Добавляем внешний ключ с каскадом
    op.create_foreign_key(
        "fk_user_subscriptions_user",
        source_table="user_subscriptions",
        referent_table="users",
        local_cols=["user_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_user_subscriptions_user",
        table_name="user_subscriptions",
        type_="foreignkey",
    )
