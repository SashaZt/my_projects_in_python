# api/schemas/stats.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseSchema


class UserStatsHistoryBase(BaseModel):
    user_id: int
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    friend_count: Optional[int] = None
    heart_count: Optional[int] = None
    video_count: Optional[int] = None
    timestamp: Optional[datetime] = None


class UserStatsHistoryCreate(UserStatsHistoryBase):
    pass


class UserStatsHistory(UserStatsHistoryBase, BaseSchema):
    pass


class NicknameHistoryBase(BaseModel):
    user_id: int
    nickname: str
    changed_at: Optional[datetime] = None


class NicknameHistoryCreate(NicknameHistoryBase):
    pass


class NicknameHistory(NicknameHistoryBase, BaseSchema):
    pass


class UniqueIdHistoryBase(BaseModel):
    user_id: int
    unique_id: str
    changed_at: Optional[datetime] = None


class UniqueIdHistoryCreate(UniqueIdHistoryBase):
    pass


class UniqueIdHistory(UniqueIdHistoryBase, BaseSchema):
    pass
