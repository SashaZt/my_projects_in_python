# api/schemas/live.py
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from utils.time_utils import date_to_unix

from .base import BaseSchema


class LiveStreamBase(BaseModel):
    user_id: int
    room_id: str
    start_time: Optional[int] = None  # Unix timestamp
    end_time: Optional[int] = None    # Unix timestamp
    diamonds: Optional[int] = None
    duration: Optional[int] = None


class LiveStreamCreate(LiveStreamBase):
    pass


class LiveStreamUpdate(BaseModel):
    end_time: Optional[int] = None
    diamonds: Optional[int] = None
    duration: Optional[int] = None


class LiveStream(LiveStreamBase, BaseSchema):
    pass


class DailyLiveAnalyticsBase(BaseModel):
    user_id: int
    date: Optional[int] = None  # Unix timestamp
    diamonds_total: Optional[int] = None
    live_duration_total: Optional[int] = None
    
    # Добавляем валидатор для автоматического преобразования даты в Unix timestamp
    @validator('date', pre=True)
    def validate_date(cls, v):
        if v is None:
            return None
            
        # Если это уже число, оставляем как есть
        if isinstance(v, int):
            return v
            
        # Если это строка даты в формате YYYY-MM-DD
        if isinstance(v, str):
            try:
                d = datetime.strptime(v, "%Y-%m-%d").date()
                return date_to_unix(d)
            except ValueError:
                pass
                
        # Если это объект date
        if isinstance(v, date):
            return date_to_unix(v)
            
        # Если это объект datetime
        if isinstance(v, datetime):
            return date_to_unix(v.date())
            
        # Если ничего не подошло, возвращаем как есть (будет ошибка валидации)
        return v


class DailyLiveAnalyticsCreate(DailyLiveAnalyticsBase):
    pass


class DailyLiveAnalyticsUpdate(BaseModel):
    diamonds_total: Optional[int] = None
    live_duration_total: Optional[int] = None


class DailyLiveAnalytics(DailyLiveAnalyticsBase, BaseSchema):
    pass