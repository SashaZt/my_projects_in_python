# api/endpoints/live.py
from typing import List
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.live import (
    LiveStream, LiveStreamCreate, LiveStreamUpdate,
    DailyLiveAnalytics, DailyLiveAnalyticsCreate
)
from core.database import get_db
from core.logger import logger
from services.live_service import LiveService
from services.user_service import UserService

router = APIRouter()


@router.post("/streams", response_model=LiveStream)
async def create_live_stream(
    stream: LiveStreamCreate,
    db: AsyncSession = Depends(get_db)
):
    """Добавление информации о новой прямой трансляции"""
    user_service = UserService(db)
    live_service = LiveService(db)
    
    # Проверяем существование пользователя
    user = await user_service.get_by_id(stream.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return await live_service.create_stream(stream)


@router.get("/streams/{user_id}", response_model=List[LiveStream])
async def get_user_streams(
    user_id: int,
    from_date: datetime = None,
    to_date: datetime = None,
    db: AsyncSession = Depends(get_db)
):
    """Получение истории прямых трансляций пользователя за период"""
    live_service = LiveService(db)
    return await live_service.get_user_streams(user_id, from_date, to_date)


@router.post("/analytics", response_model=DailyLiveAnalytics)
async def create_daily_analytics(
    analytics: DailyLiveAnalyticsCreate,
    db: AsyncSession = Depends(get_db)
):
    """Добавление дневной аналитики по прямым трансляциям"""
    user_service = UserService(db)
    live_service = LiveService(db)
    
    # Проверяем существование пользователя
    user = await user_service.get_by_id(analytics.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return await live_service.create_daily_analytics(analytics)


@router.get("/analytics/{user_id}", response_model=List[DailyLiveAnalytics])
async def get_user_analytics(
    user_id: int,
    from_date: date = None,
    to_date: date = None,
    db: AsyncSession = Depends(get_db)
):
    """Получение дневной аналитики по прямым трансляциям пользователя за период"""
    live_service = LiveService(db)
    return await live_service.get_user_analytics(user_id, from_date, to_date)


@router.post("/import-bulk", response_model=List[LiveStream])
async def import_bulk_live_data(
    tiktok_id: str,
    streams_data: List[dict],
    db: AsyncSession = Depends(get_db)
):
    """Массовый импорт данных о прямых трансляциях для пользователя"""
    user_service = UserService(db)
    live_service = LiveService(db)
    
    # Проверяем существование пользователя
    user = await user_service.get_by_tiktok_id(tiktok_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return await live_service.import_bulk_streams(user.id, streams_data)