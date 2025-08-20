"""add user_subscriptions

Revision ID: ed2cf11b0707
Revises: aec467c0ec50
Create Date: 2025-08-20 15:05:41.392135

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = 'ed2cf11b0707'
down_revision: Union[str, Sequence[str], None] = 'aec467c0ec50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_subscriptions",
        sa.Column("user_id", sa.BigInteger(), primary_key=True, nullable=False),
        sa.Column("news_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("meetings_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("important_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", mysql.DATETIME(fsp=6), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(6)")),
        sa.Column("updated_at", mysql.DATETIME(fsp=6), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP(6)")),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    # Для корректного auto-update таймстампа
    op.execute(
        "ALTER TABLE user_subscriptions "
        "MODIFY updated_at DATETIME(6) NOT NULL "
        "DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
    )

    # (опционально) FK, если нужно жёстко связать с users.id
    # op.create_foreign_key(
    #     "fk_user_subscriptions__user",
    #     "user_subscriptions", "users",
    #     ["user_id"], ["id"],
    #     ondelete="CASCADE", onupdate="CASCADE"
    # )


def downgrade() -> None:
    # op.drop_constraint("fk_user_subscriptions__user", "user_subscriptions", type_="foreignkey")
    op.drop_table("user_subscriptions")
