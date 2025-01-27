"""Add message_id to TelegramMessage

Revision ID: 90e1722c3467
Revises: 97840eacc277
Create Date: 2025-01-27 11:19:00.115298

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "90e1722c3467"
down_revision: Union[str, None] = "97840eacc277"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str, conn) -> bool:
    """Проверяет существование столбца в таблице."""
    inspector = Inspector.from_engine(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    conn = op.get_bind()

    # Добавляем столбец message_id, если он не существует
    if not column_exists("telegram_messages", "message_id", conn):
        op.add_column(
            "telegram_messages",
            sa.Column("message_id", sa.BigInteger(), nullable=False),
        )

    # Изменяем типы данных других колонок
    op.alter_column(
        "telegram_messages",
        "reply_to",
        existing_type=mysql.INTEGER(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )
    op.alter_column(
        "telegram_messages",
        "chat_id",
        existing_type=mysql.INTEGER(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )

    # Добавляем уникальное ограничение для message_id
    op.create_unique_constraint(None, "telegram_messages", ["message_id"])

    # Удаляем старый foreign key (если он существует)
    op.drop_constraint(
        "telegram_messages_ibfk_3", "telegram_messages", type_="foreignkey"
    )


def downgrade() -> None:
    # Откат изменений
    op.create_foreign_key(
        "telegram_messages_ibfk_3",
        "telegram_messages",
        "telegram_messages",
        ["reply_to"],
        ["id"],
    )
    op.drop_constraint(None, "telegram_messages", type_="unique")
    op.alter_column(
        "telegram_messages",
        "chat_id",
        existing_type=sa.BigInteger(),
        type_=mysql.INTEGER(),
        existing_nullable=True,
    )
    op.alter_column(
        "telegram_messages",
        "reply_to",
        existing_type=sa.BigInteger(),
        type_=mysql.INTEGER(),
        existing_nullable=True,
    )
    op.drop_column("telegram_messages", "message_id")
