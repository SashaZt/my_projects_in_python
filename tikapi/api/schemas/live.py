# api/schemas/live.py
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseSchema


class LiveStreamBase(BaseModel):
    user_id: int
    room_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    diamonds: Optional[int] = None
    duration: Optional[int] = None


class LiveStreamCreate(LiveStreamBase):
    pass


class LiveStreamUpdate(BaseModel):
    end_time: Optional[datetime] = None
    diamonds: Optional[int] = None
    duration: Optional[int] = None


class LiveStream(LiveStreamBase, BaseSchema):
    pass


class DailyLiveAnalyticsBase(BaseModel):
    user_id: int
    date: date
    diamonds_total: Optional[int] = None
    live_duration_total: Optional[int] = None


class DailyLiveAnalyticsCreate(DailyLiveAnalyticsBase):
    pass


class DailyLiveAnalyticsUpdate(BaseModel):
    diamonds_total: Optional[int] = None
    live_duration_total: Optional[int] = None


class DailyLiveAnalytics(DailyLiveAnalyticsBase, BaseSchema):
    pass
