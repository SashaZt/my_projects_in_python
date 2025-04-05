# api/models/stats.py
from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import datetime
import time


class UserStatsHistory(Base, BaseModel):
    __tablename__ = 'user_stats_history'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    follower_count = Column(Integer)
    following_count = Column(Integer)
    friend_count = Column(Integer)
    heart_count = Column(BigInteger)
    video_count = Column(Integer)
    timestamp = Column(BigInteger, default=lambda: int(time.time()), index=True)
    
    # Отношения
    user = relationship("User", back_populates="stats_history")


class NicknameHistory(Base, BaseModel):
    __tablename__ = 'nickname_history'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    nickname = Column(String(100), nullable=False)
    # changed_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    changed_at = Column(BigInteger, default=lambda: int(time.time()), index=True)

    
    # Отношения
    user = relationship("User", back_populates="nickname_history")


class UniqueIdHistory(Base, BaseModel):
    __tablename__ = 'unique_id_history'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    unique_id = Column(String(100), nullable=False)
    # changed_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    changed_at = Column(BigInteger, default=lambda: int(time.time()), index=True)
    
    # Отношения
    user = relationship("User", back_populates="unique_id_history")