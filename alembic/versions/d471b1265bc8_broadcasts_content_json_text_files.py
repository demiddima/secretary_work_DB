"""broadcasts.content -> JSON {text, files}

Revision ID: d471b1265bc8
Revises: e064dd9f46f4
Create Date: 2025-08-23 20:09:04.753302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd471b1265bc8'
down_revision: Union[str, Sequence[str], None] = 'e064dd9f46f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
