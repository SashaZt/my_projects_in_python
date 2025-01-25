"""Sync existing tables and add new migrations

Revision ID: 259e6e460e3b
Revises: b220bc9324d3
Create Date: 2025-01-25 17:23:13.135942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '259e6e460e3b'
down_revision: Union[str, None] = 'b220bc9324d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('telegram_messages',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('sender_name', sa.String(length=255), nullable=True),
    sa.Column('sender_username', sa.String(length=255), nullable=True),
    sa.Column('sender_id', sa.BigInteger(), nullable=True),
    sa.Column('sender_phone', sa.String(length=20), nullable=True),
    sa.Column('sender_type', sa.String(length=50), nullable=True),
    sa.Column('recipient_name', sa.String(length=255), nullable=True),
    sa.Column('recipient_username', sa.String(length=255), nullable=True),
    sa.Column('recipient_id', sa.BigInteger(), nullable=True),
    sa.Column('recipient_phone', sa.String(length=20), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('telegram_messages')
    # ### end Alembic commands ###
