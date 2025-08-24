"""rename broadcasts.content_html to content; drop broadcast_media

Revision ID: e064dd9f46f4
Revises: ff2520347a8e
Create Date: 2025-08-23 19:59:51.688546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e064dd9f46f4'
down_revision: Union[str, Sequence[str], None] = 'ff2520347a8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) broadcasts.content_html → broadcasts.content (тип TEXT сохраняем)
    op.alter_column(
        "broadcasts",
        "content_html",
        new_column_name="content",
        existing_type=sa.Text(),
        existing_nullable=False,
    )

    # 2) Удаляем индекс и таблицу broadcast_media
    # (в MySQL индексы удаляются вместе с таблицей, но явный drop_index безопасен)
    try:
        op.drop_index("ix_bmedia_broadcast_id", table_name="broadcast_media")
    except Exception:
        # индекс мог быть уже удалён / отсутствовать — пропускаем
        pass

    op.drop_table("broadcast_media")


def downgrade() -> None:
    # 1) Восстанавливаем таблицу broadcast_media (в состоянии после миграции ff2520347a8e)
    op.create_table(
        "broadcast_media",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "broadcast_id",
            sa.Integer,
            sa.ForeignKey("broadcasts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.Enum("html", "photo", "video", "document", "album", name="broadcast_media_type"),
            nullable=False,
        ),
        sa.Column("payload_json", sa.JSON, nullable=False),
        sa.Column("position", sa.SmallInteger, nullable=False, server_default="0"),
        # после ff252 created_at стал просто NOT NULL без дефолта/таймзоны
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
    )
    op.create_index("ix_bmedia_broadcast_id", "broadcast_media", ["broadcast_id"])

    # 2) broadcasts.content → broadcasts.content_html
    op.alter_column(
        "broadcasts",
        "content",
        new_column_name="content_html",
        existing_type=sa.Text(),
        existing_nullable=False,
    )
