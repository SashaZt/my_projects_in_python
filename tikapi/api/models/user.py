# api/models/user.py
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DateTime, BigInteger, Date
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class User(Base, BaseModel):
    __tablename__ = 'users'
    
    tik_tok_id = Column(String(50), nullable=False, unique=True, index=True)
    nickname = Column(String(100), index=True)
    unique_id = Column(String(100), nullable=False, index=True)
    avatar_medium = Column(Text)
    following_visibility = Column(Integer)
    is_under_age_18 = Column(Boolean)
    open_favorite = Column(Boolean)
    private_account = Column(Boolean)
    signature = Column(Text)
    
    # Отношения
    stats_history = relationship("UserStatsHistory", back_populates="user")
    nickname_history = relationship("NicknameHistory", back_populates="user")
    unique_id_history = relationship("UniqueIdHistory", back_populates="user")
    live_streams = relationship("LiveStream", back_populates="user")
    daily_analytics = relationship("DailyLiveAnalytics", back_populates="user")