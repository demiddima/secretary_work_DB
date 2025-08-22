"""add broadcast targets/media/deliveries

Revision ID: 9e29e351585d
Revises: 183f7fd95c5d
Create Date: 2025-08-21 09:50:24.606967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e29e351585d'
down_revision: Union[str, Sequence[str], None] = '183f7fd95c5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # broadcast_targets
    op.create_table(
        "broadcast_targets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("broadcast_id", sa.Integer, sa.ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum("ids", "sql", "kind", name="broadcast_target_type"), nullable=False),
        sa.Column("user_ids_json", sa.JSON, nullable=True),
        sa.Column("sql_text", sa.Text, nullable=True),
        sa.Column("kind", sa.Enum("news", "meetings", "important", name="broadcast_kind_target"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_btarget_broadcast_id", "broadcast_targets", ["broadcast_id"])

    # broadcast_media
    op.create_table(
        "broadcast_media",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("broadcast_id", sa.Integer, sa.ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum("html", "photo", "video", "document", "album", name="broadcast_media_type"), nullable=False),
        sa.Column("payload_json", sa.JSON, nullable=False),
        sa.Column("position", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bmedia_broadcast_id", "broadcast_media", ["broadcast_id"])

    # broadcast_deliveries
    op.create_table(
        "broadcast_deliveries",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("broadcast_id", sa.Integer, sa.ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("status", sa.Enum("pending", "sent", "failed", "skipped", name="delivery_status"), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.String(255), nullable=True),
        sa.Column("message_id", sa.BigInteger, nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bdeliveries_broadcast_id", "broadcast_deliveries", ["broadcast_id"])
    op.create_index("ix_bdeliveries_broadcast_status", "broadcast_deliveries", ["broadcast_id", "status"])
    op.create_unique_constraint("uq_bdeliveries_broadcast_user", "broadcast_deliveries", ["broadcast_id", "user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_bdeliveries_broadcast_user", "broadcast_deliveries", type_="unique")
    op.drop_index("ix_bdeliveries_broadcast_status", table_name="broadcast_deliveries")
    op.drop_index("ix_bdeliveries_broadcast_id", table_name="broadcast_deliveries")
    op.drop_table("broadcast_deliveries")

    op.drop_index("ix_bmedia_broadcast_id", table_name="broadcast_media")
    op.drop_table("broadcast_media")

    op.drop_index("ix_btarget_broadcast_id", table_name="broadcast_targets")
    op.drop_table("broadcast_targets")
