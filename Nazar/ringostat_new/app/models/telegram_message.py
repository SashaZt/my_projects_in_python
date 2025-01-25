from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.base import Base


class TelegramMessage(Base):
    __tablename__ = "telegram_messages"  # Имя таблицы сообщений.

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )  # Уникальный идентификатор сообщения.
    sender_id = Column(
        Integer, ForeignKey("telegram_users.id"), nullable=False
    )  # ID отправителя, внешний ключ.
    recipient_id = Column(
        Integer, ForeignKey("telegram_users.id"), nullable=False
    )  # ID получателя, внешний ключ.
    message = Column(Text, nullable=False)  # Текст сообщения.
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )  # Дата и время создания сообщения.

    # Связи
    sender = relationship(
        "TelegramUser", foreign_keys=[sender_id], backref="messages_sent"
    )
    recipient = relationship(
        "TelegramUser", foreign_keys=[recipient_id], backref="messages_received"
    )
