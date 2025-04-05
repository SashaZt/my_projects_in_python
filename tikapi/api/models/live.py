# api/models/live.py
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Date, func,BigInteger
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import time

class LiveStream(Base, BaseModel):
    __tablename__ = 'live_streams'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    room_id = Column(String(100), nullable=False, index=True)
    start_time = Column(BigInteger, index=True)
    end_time = Column(BigInteger)
    diamonds = Column(Integer)
    duration = Column(Integer)  # в секундах
    
    # Отношения
    user = relationship("User", back_populates="live_streams")


class DailyLiveAnalytics(Base, BaseModel):
    __tablename__ = 'daily_live_analytics'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    # date = Column(Date, nullable=False, index=True)
    date = Column(BigInteger, nullable=False, index=True)  # Unix timestamp полночи дня
    diamonds_total = Column(Integer)
    live_duration_total = Column(Integer)  # в секундах
    
    # Отношения
    user = relationship("User", back_populates="daily_analytics")