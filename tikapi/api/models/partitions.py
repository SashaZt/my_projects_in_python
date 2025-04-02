# api/models/partitions.py
from sqlalchemy import Column, Integer, BigInteger, ForeignKey, DateTime, func
from .base import Base

class UserStatsHistoryPartitioned(Base):
    __tablename__ = 'user_stats_history_partitioned'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    follower_count = Column(Integer)
    following_count = Column(Integer)
    friend_count = Column(Integer)
    heart_count = Column(BigInteger)
    video_count = Column(Integer)
    timestamp = Column(DateTime(timezone=True), primary_key=True, default=func.now())
    
    # Примечание: партиционирование настраивается на уровне PostgreSQL,
    # SQLAlchemy самостоятельно не управляет партициями