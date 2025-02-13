# app/schemas/olx_messages.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Attachment(BaseModel):
    url: Optional[str] = None

class Thread(BaseModel):
    id: int
    advert_id: int
    interlocutor_id: int
    total_count: int
    unread_count: int
    created_at: datetime
    is_favourite: bool

class Message(BaseModel):
    id: int
    thread_id: int
    created_at: datetime
    type: str
    text: str
    attachments: Optional[List[Attachment]] = None
    is_read: bool

class MessageCreate(BaseModel):
    text: str
    attachments: Optional[List[Attachment]] = None