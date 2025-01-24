from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime
from app.core.base import Base  # Убедитесь, что Base подключен корректно


class TelegramMessage(Base):
    __tablename__ = "telegram_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_name = Column(String(255))
    sender_username = Column(String(255))
    sender_id = Column(BigInteger)
    sender_phone = Column(String(20))
    sender_type = Column(String(50))
    recipient_name = Column(String(255))
    recipient_username = Column(String(255))
    recipient_id = Column(BigInteger)
    recipient_phone = Column(String(20))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
