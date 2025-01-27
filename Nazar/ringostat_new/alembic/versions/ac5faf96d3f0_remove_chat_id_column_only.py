"""remove_chat_id_column_only

Revision ID: ac5faf96d3f0
Revises: 90e1722c3467
Create Date: 2025-01-27 16:08:21.922346

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "ac5faf96d3f0"  # Используйте актуальный ID
down_revision: Union[str, None] = "90e1722c3467"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("telegram_messages", "chat_id")


def downgrade() -> None:
    op.add_column(
        "telegram_messages", sa.Column("chat_id", sa.BigInteger(), nullable=True)
    )
