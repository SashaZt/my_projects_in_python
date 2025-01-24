from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from typing import Any, List
from pydantic import BaseModel
from typing import Optional, Union
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
        from_attributes = True  # Замена orm_mode


class ContactFilter(BaseModel):
    searchString: Optional[str] = None
    statusFilter: Optional[str] = None
    contactFilter: Optional[str] = None
    start: Optional[Union[str, datetime]] = None  # Разрешаем строку или datetime
    end: Optional[Union[str, datetime]] = None  # Разрешаем строку или datetime
    activeRecords: Optional[Union[bool, str]] = None  # Разрешаем bool или строку
    limit: int = 10
    page: int = 1
    sortBy: Optional[str] = None
    sortOrder: Optional[str] = "asc"


class PaginatedResponse(BaseModel):
    data: List[Any]
    totalPages: int
    currentPage: int


class ContactMini(BaseModel):
    id: int
    username: str
