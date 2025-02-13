# app/models/olx_token.py

from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base

class OLXToken(Base):
    __tablename__ = "olx_tokens"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String(255), nullable=False)
    refresh_token = Column(String(255), nullable=False)
    expires_in = Column(Integer)
    token_type = Column(String(50))
    scope = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())