"""BigInt reservation timestamps

Revision ID: 20250323456789
Revises: bf5b421d85b1
Create Date: 2025-03-23 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20250323456789'
down_revision: Union[str, None] = 'bf5b421d85b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Изменяем тип столбцов в таблице reservations
    try:
        op.alter_column('reservations', 'bookedAt',
                      existing_type=sa.Integer(),
                      type_=sa.BigInteger(),
                      existing_nullable=False)
    except Exception as e:
        print(f"Ошибка при изменении столбца reservations.bookedAt: {e}")
    
    try:
        op.alter_column('reservations', 'modifiedAt',
                      existing_type=sa.Integer(),
                      type_=sa.BigInteger(),
                      existing_nullable=False)
    except Exception as e:
        print(f"Ошибка при изменении столбца reservations.modifiedAt: {e}")
    
    # Изменяем тип столбцов в таблице room_reservations
    try:
        op.alter_column('room_reservations', 'arrival',
                      existing_type=sa.Integer(),
                      type_=sa.BigInteger(),
                      existing_nullable=False)
    except Exception as e:
        print(f"Ошибка при изменении столбца room_reservations.arrival: {e}")
    
    try:
        op.alter_column('room_reservations', 'departure',
                      existing_type=sa.Integer(),
                      type_=sa.BigInteger(),
                      existing_nullable=False)
    except Exception as e:
        print(f"Ошибка при изменении столбца room_reservations.departure: {e}")


def downgrade() -> None:
    # Возвращаем типы столбцов к Integer
    try:
        op.alter_column('room_reservations', 'departure',
                      existing_type=sa.BigInteger(),
                      type_=sa.Integer(),
                      existing_nullable=False)
    except Exception as e:
        print(f"Ошибка при возвращении столбца room_reservations.departure: {e}")
    
    try:
        op.alter_column('room_reservations', 'arrival',
                      existing_type=sa.BigInteger(),
                      type_=sa.Integer(),
                      existing_nullable=False)
    except Exception as e:
        print(f"Ошибка при возвращении столбца room_reservations.arrival: {e}")
    
    try:
        op.alter_column('reservations', 'modifiedAt',
                      existing_type=sa.BigInteger(),
                      type_=sa.Integer(),
                      existing_nullable=False)
    except Exception as e:
        print(f"Ошибка при возвращении столбца reservations.modifiedAt: {e}")
    
    try:
        op.alter_column('reservations', 'bookedAt',
                      existing_type=sa.BigInteger(),
                      type_=sa.Integer(),
                      existing_nullable=False)
    except Exception as e:
        print(f"Ошибка при возвращении столбца reservations.bookedAt: {e}")