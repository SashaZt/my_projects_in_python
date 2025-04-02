# api/schemas/user.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

from .base import BaseSchema


class UserBase(BaseModel):
    tik_tok_id: str
    nickname: Optional[str] = None
    unique_id: str
    avatar_medium: Optional[str] = None
    following_visibility: Optional[int] = None
    is_under_age_18: Optional[bool] = None
    open_favorite: Optional[bool] = None
    private_account: Optional[bool] = None
    signature: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    unique_id: Optional[str] = None
    avatar_medium: Optional[str] = None
    following_visibility: Optional[int] = None
    is_under_age_18: Optional[bool] = None
    open_favorite: Optional[bool] = None
    private_account: Optional[bool] = None
    signature: Optional[str] = None


class User(UserBase, BaseSchema):
    pass


class UserDetail(User):
    stats_history: List["UserStatsHistory"] = []
    nickname_history: List["NicknameHistory"] = []
    unique_id_history: List["UniqueIdHistory"] = []
    live_streams: List["LiveStream"] = []
    daily_analytics: List["DailyLiveAnalytics"] = []


from .live import DailyLiveAnalytics, LiveStream
from .stats import NicknameHistory, UniqueIdHistory, UserStatsHistory

UserDetail.update_forward_refs()
