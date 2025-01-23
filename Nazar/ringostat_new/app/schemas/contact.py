from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ContactCreate(BaseModel):
    contact_id: Optional[int] = None  # Поле для идентификации контакта
    username: str
    contact_type: str
    contact_status: str
    manager: Optional[str] = None
    userphone: Optional[str] = None
    useremail: Optional[str] = None
    usersite: Optional[str] = None
    comment: Optional[str] = None


class ContactResponse(BaseModel):
    id: int
    username: str
    contact_type: str
    contact_status: str
    manager: Optional[str]
    userphone: Optional[str]
    useremail: Optional[str]
    usersite: Optional[str]
    comment: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
