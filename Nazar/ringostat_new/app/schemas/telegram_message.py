from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TelegramMessageCreate(BaseModel):
    sender_name: Optional[str]
    sender_username: Optional[str]
    sender_id: Optional[int]
    sender_phone: Optional[str]
    sender_type: Optional[str]
    recipient_name: Optional[str]
    recipient_username: Optional[str]
    recipient_id: Optional[int]
    recipient_phone: Optional[str]
    message: Optional[str]

    class Config:
        orm_mode = True


class TelegramMessageResponse(BaseModel):
    sender_name: Optional[str]
    sender_username: Optional[str]
    sender_id: Optional[int]
    sender_phone: Optional[str]
    sender_type: Optional[str]
    recipient_name: Optional[str]
    recipient_username: Optional[str]
    recipient_id: Optional[int]
    recipient_phone: Optional[str]
    message: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
