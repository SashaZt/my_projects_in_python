# api/models/__init__.py
from .base import Base, BaseModel
from .user import User
from .stats import UserStatsHistory, NicknameHistory, UniqueIdHistory
from .live import LiveStream, DailyLiveAnalytics
from .partitions import UserStatsHistoryPartitioned

# Для удобства импорта
__all__ = [
    'Base', 'BaseModel',
    'User',
    'UserStatsHistory', 'NicknameHistory', 'UniqueIdHistory',
    'LiveStream', 'DailyLiveAnalytics',
    'UserStatsHistoryPartitioned'
]