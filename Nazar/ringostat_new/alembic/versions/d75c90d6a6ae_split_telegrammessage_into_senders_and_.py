"""Split TelegramMessage into senders and recipients

Revision ID: d75c90d6a6ae
Revises: 6577be9f8427
Create Date: 2025-01-25 16:17:27.159584

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "d75c90d6a6ae"
down_revision: Union[str, None] = "6577be9f8427"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблиц telegram_senders и telegram_recipients
    op.create_table(
        "telegram_senders",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=True),
    )

    op.create_table(
        "telegram_recipients",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
    )

    # Изменение типа данных sender_id и recipient_id
    op.alter_column(
        "telegram_messages",
        "sender_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.alter_column(
        "telegram_messages",
        "recipient_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )


def downgrade() -> None:
    # Удаление таблиц telegram_senders и telegram_recipients
    op.drop_table("telegram_senders")
    op.drop_table("telegram_recipients")
