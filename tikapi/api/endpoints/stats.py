# api/endpoints/stats.py
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.stats import (
    UserStatsHistory, UserStatsHistoryCreate,
    NicknameHistory, NicknameHistoryCreate,
    UniqueIdHistory, UniqueIdHistoryCreate
)
from core.database import get_db
from core.logger import logger
from services.stats_service import StatsService
from services.user_service import UserService

router = APIRouter()


@router.post("/user-stats", response_model=UserStatsHistory)
async def create_user_stats(
    stats: UserStatsHistoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Добавление новой записи статистики пользователя"""
    user_service = UserService(db)
    stats_service = StatsService(db)
    
    # Проверяем существование пользователя
    user = await user_service.get_by_id(stats.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return await stats_service.create_stats(stats)


@router.get("/user-stats/{user_id}", response_model=List[UserStatsHistory])
async def get_user_stats(
    user_id: int,
    from_date: datetime = None,
    to_date: datetime = None,
    db: AsyncSession = Depends(get_db)
):
    """Получение истории статистики пользователя за период"""
    stats_service = StatsService(db)
    return await stats_service.get_user_stats(user_id, from_date, to_date)


@router.post("/nickname-history", response_model=NicknameHistory)
async def create_nickname_history(
    history: NicknameHistoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Добавление новой записи в историю изменений никнейма"""
    user_service = UserService(db)
    stats_service = StatsService(db)
    
    # Проверяем существование пользователя
    user = await user_service.get_by_id(history.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return await stats_service.create_nickname_history(history)


@router.post("/uniqueid-history", response_model=UniqueIdHistory)
async def create_uniqueid_history(
    history: UniqueIdHistoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Добавление новой записи в историю изменений unique_id"""
    user_service = UserService(db)
    stats_service = StatsService(db)
    
    # Проверяем существование пользователя
    user = await user_service.get_by_id(history.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return await stats_service.create_uniqueid_history(history)