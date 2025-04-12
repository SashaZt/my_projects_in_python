# api/schemas/__init__.py
from .base import BaseSchema
from .user import User, UserCreate, UserUpdate, UserDetail
from .stats import (
    UserStatsHistory,
    UserStatsHistoryCreate,
    NicknameHistory,
    NicknameHistoryCreate,
    UniqueIdHistory,
    UniqueIdHistoryCreate,
)
from .live import (
    LiveStream,
    LiveStreamCreate,
    LiveStreamUpdate,
    DailyLiveAnalytics,
    DailyLiveAnalyticsCreate,
    DailyLiveAnalyticsUpdate,
)

# Для удобства импорта
__all__ = [
    "BaseSchema",
    "User",
    "UserCreate",
    "UserUpdate",
    "UserDetail",
    "UserStatsHistory",
    "UserStatsHistoryCreate",
    "NicknameHistory",
    "NicknameHistoryCreate",
    "UniqueIdHistory",
    "UniqueIdHistoryCreate",
    "LiveStream",
    "LiveStreamCreate",
    "LiveStreamUpdate",
    "DailyLiveAnalytics",
    "DailyLiveAnalyticsCreate",
    "DailyLiveAnalyticsUpdate",
]
