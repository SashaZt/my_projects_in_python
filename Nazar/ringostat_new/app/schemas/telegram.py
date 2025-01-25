from pydantic import BaseModel
from typing import Optional


class UserSchema(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    telegram_id: int
    phone: Optional[str] = None


class MessageSchema(BaseModel):
    text: str


class TelegramMessageSchema(BaseModel):
    sender: UserSchema
    recipient: UserSchema
    message: MessageSchema
