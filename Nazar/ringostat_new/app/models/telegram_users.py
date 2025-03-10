#app/models/telegram_users.py
from sqlalchemy import Column, Integer, BigInteger, String
from app.core.base import Base


class TelegramUser(Base):
    __tablename__ = "telegram_users"  # Имя таблицы для пользователей.

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )  # Уникальный идентификатор пользователя.
    name = Column(String(255), nullable=True)  # Имя пользователя.
    username = Column(String(255), nullable=True)  # Username пользователя.
    telegram_id = Column(
        BigInteger, unique=True, nullable=False
    )  # Уникальный Telegram ID.
    phone = Column(String(20), nullable=True)  # Телефонный номер пользователя.
