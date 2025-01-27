from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.base import Base
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    String,
)

# Рабочая
# class TelegramMessage(Base):
#     __tablename__ = "telegram_messages"  # Имя таблицы сообщений.

#     id = Column(
#         Integer, primary_key=True, autoincrement=True
#     )  # Уникальный идентификатор сообщения.
#     sender_id = Column(
#         Integer, ForeignKey("telegram_users.id"), nullable=False
#     )  # ID отправителя, внешний ключ.
#     recipient_id = Column(
#         Integer, ForeignKey("telegram_users.id"), nullable=False
#     )  # ID получателя, внешний ключ.
#     message = Column(Text, nullable=False)  # Текст сообщения.
#     created_at = Column(
#         DateTime, default=lambda: datetime.now(timezone.utc)
#     )  # Дата и время создания сообщения.


#     # Связи
#     sender = relationship(
#         "TelegramUser", foreign_keys=[sender_id], backref="messages_sent"
#     )
#     recipient = relationship(
#         "TelegramUser", foreign_keys=[recipient_id], backref="messages_received"
#     )
# class TelegramMessage(Base):
#     __tablename__ = "telegram_messages"  # Имя таблицы сообщений.

#     id = Column(
#         Integer, primary_key=True, autoincrement=True
#     )  # Уникальный идентификатор сообщения.
#     sender_id = Column(
#         Integer, ForeignKey("telegram_users.id"), nullable=False
#     )  # ID отправителя, внешний ключ.
#     recipient_id = Column(
#         Integer, ForeignKey("telegram_users.id"), nullable=False
#     )  # ID получателя, внешний ключ.
#     message = Column(Text, nullable=False)  # Текст сообщения.
#     created_at = Column(
#         DateTime, default=lambda: datetime.now(timezone.utc)
#     )  # Дата и время создания сообщения.
#     is_read = Column(Boolean, default=False)  # Статус сообщения: прочитано или нет.
#     is_reply = Column(
#         Boolean, default=False
#     )  # Статус сообщения: является ли это ответом.
#     reply_to = Column(
#         Integer, ForeignKey("telegram_messages.id"), nullable=True
#     )  # ID сообщения, на которое отвечают.


#     # Связи
#     sender = relationship(
#         "TelegramUser", foreign_keys=[sender_id], backref="messages_sent"
#     )
#     recipient = relationship(
#         "TelegramUser", foreign_keys=[recipient_id], backref="messages_received"
#     )
#     replied_message = relationship(
#         "TelegramMessage", remote_side=[id], backref="replies"
#     )  # Связь для ответов.
# class TelegramMessage(Base):
#     __tablename__ = "telegram_messages"  # Имя таблицы сообщений.

#     id = Column(
#         Integer, primary_key=True, autoincrement=True
#     )  # Уникальный ID сообщения.
#     sender_id = Column(
#         Integer, ForeignKey("telegram_users.id"), nullable=False
#     )  # ID отправителя.
#     recipient_id = Column(
#         Integer, ForeignKey("telegram_users.id"), nullable=False
#     )  # ID получателя.
#     message = Column(Text, nullable=False)  # Текст сообщения.
#     created_at = Column(
#         DateTime, default=lambda: datetime.now(timezone.utc)
#     )  # Время создания.
#     is_read = Column(Boolean, default=False)  # Прочитано или нет.
#     is_reply = Column(Boolean, default=False)  # Является ли это ответом.
#     reply_to = Column(
#         Integer, ForeignKey("telegram_messages.id"), nullable=True
#     )  # ID сообщения, на которое ответили.
#     chat_id = Column(Integer, nullable=True)  # ID чата (группы или канала).
#     direction = Column(String(10), nullable=False, default="inbox")  # inbox/outbox.


#     # Связи
#     sender = relationship(
#         "TelegramUser", foreign_keys=[sender_id], backref="messages_sent"
#     )
#     recipient = relationship(
#         "TelegramUser", foreign_keys=[recipient_id], backref="messages_received"
#     )
#     replied_message = relationship(
#         "TelegramMessage", remote_side=[id], backref="replies"
#     )
class TelegramMessage(Base):
    __tablename__ = "telegram_messages"  # Имя таблицы сообщений.

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Уникальный ID записи в БД.
    message_id = Column(
        BigInteger, unique=True, nullable=False
    )  # Telegram ID сообщения (важно!)
    sender_id = Column(
        Integer, ForeignKey("telegram_users.id"), nullable=False
    )  # ID отправителя.
    recipient_id = Column(
        Integer, ForeignKey("telegram_users.id"), nullable=False
    )  # ID получателя.
    message = Column(Text, nullable=False)  # Текст сообщения.
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )  # Время создания.
    is_read = Column(Boolean, default=False)  # Прочитано или нет.
    is_reply = Column(Boolean, default=False)  # Является ли это ответом.
    reply_to = Column(
        BigInteger, nullable=True
    )  # Telegram ID сообщения, на которое ответили.
    direction = Column(String(10), nullable=False, default="inbox")  # inbox/outbox.

    # Связи
    sender = relationship(
        "TelegramUser", foreign_keys=[sender_id], backref="messages_sent"
    )
    recipient = relationship(
        "TelegramUser", foreign_keys=[recipient_id], backref="messages_received"
    )
