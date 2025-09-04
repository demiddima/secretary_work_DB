"""v2 Ads: tables ads & ad_random_branches

Revision ID: c312ea88549e
Revises: 3c0532540e20
Create Date: 2025-08-29 11:14:33.151829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c312ea88549e'
down_revision: Union[str, Sequence[str], None] = '3c0532540e20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "ads",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(255), nullable=False),

        sa.Column("chat_id", sa.BigInteger, nullable=False),
        sa.Column("thread_id", sa.Integer, nullable=True),

        sa.Column("content_json", sa.JSON, nullable=False, comment="{'text': str, 'files': 'csv', 'button': {'enabled': bool, 'label': str, 'url': str}, 'link_preview': bool}"),

        sa.Column("schedule_type", sa.Enum("cron", "n_days", "random", name="ad_schedule_type"), nullable=False),
        sa.Column("schedule_cron", sa.String(255), nullable=True),

        sa.Column("n_days_start_date", sa.Date, nullable=True),
        sa.Column("n_days_time", sa.Time, nullable=True),
        sa.Column("n_days_interval", sa.SmallInteger, nullable=True),

        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("delete_previous", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("dedupe_minute", sa.Boolean, nullable=False, server_default=sa.text("1")),

        sa.Column("auto_delete_ttl_hours", sa.SmallInteger, nullable=True),
        sa.Column("auto_delete_cron", sa.String(255), nullable=True),

        sa.Column("last_message_id", sa.BigInteger, nullable=True),

        sa.Column("created_by", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
    )
    op.create_index("ix_ads_target", "ads", ["chat_id", "thread_id", "enabled"])
    op.create_index("ix_ads_schedule_type", "ads", ["schedule_type", "enabled"])

    op.create_table(
        "ad_random_branches",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("chat_id", sa.BigInteger, nullable=False),
        sa.Column("thread_id", sa.Integer, nullable=True),
        sa.Column("window_from", sa.Time, nullable=False),
        sa.Column("window_to", sa.Time, nullable=False),
        sa.Column("rebuild_time", sa.Time, nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
    )
    op.create_unique_constraint(
        "uq_ad_random_branch_chat_thread",
        "ad_random_branches",
        ["chat_id", "thread_id"],
    )
    op.create_index("ix_random_branch_enabled", "ad_random_branches", ["enabled"])


def downgrade():
    op.drop_index("ix_random_branch_enabled", table_name="ad_random_branches")
    op.drop_constraint("uq_ad_random_branch_chat_thread", "ad_random_branches", type_="unique")
    op.drop_table("ad_random_branches")

    op.drop_index("ix_ads_schedule_type", table_name="ads")
    op.drop_index("ix_ads_target", table_name="ads")
    op.drop_table("ads")

    # drop enum explicitly for some MySQL setups
    try:
        op.execute("DROP TYPE ad_schedule_type")
    except Exception:
        pass
