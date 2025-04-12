# api/schemas/base.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    id: Optional[int] = None
    created_at: Optional[int] = None  # Unix timestamp
    updated_at: Optional[int] = None  # Unix timestamp
    # Опционально: добавить читаемые поля
    created_at_readable: Optional[str] = None
    updated_at_readable: Optional[str] = None
    
   

    class Config:
        orm_mode = True
        from_attributes = True  # для новых версий Pydantic
