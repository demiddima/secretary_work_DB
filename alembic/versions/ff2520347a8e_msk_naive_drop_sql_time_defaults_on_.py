"""msk-naive: drop SQL time defaults/ON UPDATE

Revision ID: ff2520347a8e
Revises: 9e29e351585d
Create Date: 2025-08-23 08:46:07.032997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff2520347a8e'
down_revision: Union[str, Sequence[str], None] = '9e29e351585d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Чаты / участники
    op.execute("ALTER TABLE chats                   MODIFY added_at     DATETIME NOT NULL")
    op.execute("ALTER TABLE user_memberships        MODIFY joined_at    DATETIME NOT NULL")
    op.execute("ALTER TABLE links                   MODIFY created_at   DATETIME NOT NULL")
    op.execute("ALTER TABLE user_algorithm_progress MODIFY updated_at   DATETIME NOT NULL")
    op.execute("ALTER TABLE settings                MODIFY updated_at   DATETIME NOT NULL")

    # Подписки (с микросекундами)
    op.execute("ALTER TABLE user_subscriptions      MODIFY created_at   DATETIME(6) NOT NULL")
    op.execute("ALTER TABLE user_subscriptions      MODIFY updated_at   DATETIME(6) NOT NULL")

    # Рассылки
    op.execute("ALTER TABLE broadcasts              MODIFY created_at   DATETIME NOT NULL")
    op.execute("ALTER TABLE broadcasts              MODIFY updated_at   DATETIME NOT NULL")
    op.execute("ALTER TABLE broadcast_targets       MODIFY created_at   DATETIME NOT NULL")
    op.execute("ALTER TABLE broadcast_media         MODIFY created_at   DATETIME NOT NULL")
    op.execute("ALTER TABLE broadcast_deliveries    MODIFY created_at   DATETIME NOT NULL")


def downgrade() -> None:
    # Возврат дефолтов/ON UPDATE не делаем, оставляем "чистые" DATETIME
    pass
