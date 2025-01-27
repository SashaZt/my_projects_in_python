from pydantic import BaseModel
from typing import Optional


class UserSchema(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    telegram_id: int
    phone: Optional[str] = None


class MessageSchema(BaseModel):
    message_id: int
    text: str
    is_reply: bool = False
    reply_to: Optional[int] = None
    read: bool = False
    direction: str  # Добавляем это поле


class TelegramMessageSchema(BaseModel):
    sender: UserSchema
    recipient: UserSchema
    message: MessageSchema


class MessageReadSchema(BaseModel):
    sender_id: int
    recipient_id: int
    max_id: int
