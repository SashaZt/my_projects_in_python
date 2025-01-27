"""Create contacts table

Revision ID: 84cc3a9af94c
Revises: fda2e2f56070
Create Date: 2025-01-23 15:19:15.269704

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "84cc3a9af94c"
down_revision: Union[str, None] = "fda2e2f56070"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("contact_type", sa.String(length=255), nullable=False),
        sa.Column("contact_status", sa.String(length=255), nullable=False),
        sa.Column("manager", sa.String(length=255), nullable=True),
        sa.Column("userphone", sa.String(length=20), nullable=True),
        sa.Column("useremail", sa.String(length=255), nullable=True),
        sa.Column("usersite", sa.String(length=255), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # Добавление индексов для ускорения поиска по полям
    # Индекс по полю username для быстрого поиска контактов по имени пользователя
    # Use MySQL-specific index creation with explicit length
    op.execute("CREATE INDEX ix_contacts_username ON contacts (username(191))")
    op.execute("CREATE INDEX ix_contacts_contact_type ON contacts (contact_type(191))")

    # Вы можете добавить больше индексов по другим полям, если это необходимо
    # Например:
    # op.create_index(op.f("ix_contacts_useremail"), "contacts", ["useremail"], unique=False)
    # op.create_index(op.f("ix_contacts_userphone"), "contacts", ["userphone"], unique=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("contacts")
    # При понижении версии миграции, индексы автоматически удаляются вместе с таблицей
    # ### end Alembic commands ###