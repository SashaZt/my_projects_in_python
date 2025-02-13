# app/schemas/olx.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TokenBase(BaseModel):
    access_token: str
    expires_in: int
    token_type: str
    scope: str
    refresh_token: str

class TokenCreate(TokenBase):
    pass

class TokenResponse(TokenBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TokenDB(TokenBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True