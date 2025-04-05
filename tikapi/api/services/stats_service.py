# services/stats_service.py
from typing import List, Optional
from datetime import datetime
import time
from utils.time_utils import now_unix
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.stats import UserStatsHistory, NicknameHistory, UniqueIdHistory
from schemas.stats import (
    UserStatsHistoryCreate, NicknameHistoryCreate, UniqueIdHistoryCreate
)


class StatsService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_stats(self, stats_data: UserStatsHistoryCreate) -> UserStatsHistory:
        """Создание новой записи статистики пользователя"""
        stats = UserStatsHistory(
            user_id=stats_data.user_id,
            follower_count=stats_data.follower_count,
            following_count=stats_data.following_count,
            friend_count=stats_data.friend_count,
            heart_count=stats_data.heart_count,
            video_count=stats_data.video_count,
            timestamp=stats_data.timestamp or now_unix()
        )
        
        self.db.add(stats)
        await self.db.commit()
        await self.db.refresh(stats)
        return stats
    
    async def get_user_stats(
    self, user_id: int, from_date: Optional[int] = None, to_date: Optional[int] = None
) -> List[UserStatsHistory]:
        """Получение истории статистики пользователя за период"""
        query = select(UserStatsHistory).where(UserStatsHistory.user_id == user_id)
        
        if from_date:
            query = query.where(UserStatsHistory.timestamp >= from_date)
        if to_date:
            query = query.where(UserStatsHistory.timestamp <= to_date)
        
        # Сортировка по времени
        query = query.order_by(UserStatsHistory.timestamp.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_nickname_history(self, history_data: NicknameHistoryCreate) -> NicknameHistory:
        """Создание новой записи в истории изменений никнейма"""
        history = NicknameHistory(
            user_id=history_data.user_id,
            nickname=history_data.nickname,
            changed_at=history_data.changed_at or now_unix()
        )
        
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)
        return history
    
    async def get_nickname_history(self, user_id: int) -> List[NicknameHistory]:
        """Получение истории изменений никнейма пользователя"""
        query = select(NicknameHistory).where(NicknameHistory.user_id == user_id)
        query = query.order_by(NicknameHistory.changed_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_uniqueid_history(self, history_data: UniqueIdHistoryCreate) -> UniqueIdHistory:
        """Создание новой записи в истории изменений unique_id"""
        history = UniqueIdHistory(
            user_id=history_data.user_id,
            unique_id=history_data.unique_id,
            changed_at=history_data.changed_at or datetime.now()
        )
        
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)
        return history
    
    async def get_uniqueid_history(self, user_id: int) -> List[UniqueIdHistory]:
        """Получение истории изменений unique_id пользователя"""
        query = select(UniqueIdHistory).where(UniqueIdHistory.user_id == user_id)
        query = query.order_by(UniqueIdHistory.changed_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def compare_and_update_stats(self, user_id: int, current_stats: dict) -> bool:
        """
        Сравнивает текущую статистику с последней сохраненной и создает новую запись,
        если есть изменения.
        """
        # Получаем последнюю запись статистики
        query = select(UserStatsHistory).where(UserStatsHistory.user_id == user_id)
        query = query.order_by(UserStatsHistory.timestamp.desc()).limit(1)
        
        result = await self.db.execute(query)
        last_stats = result.scalars().first()
        
        # Если нет предыдущих записей или есть изменения, сохраняем новую
        if not last_stats or (
            last_stats.follower_count != current_stats.get("follower_count") or
            last_stats.following_count != current_stats.get("following_count") or
            last_stats.friend_count != current_stats.get("friend_count") or
            last_stats.heart_count != current_stats.get("heart_count") or
            last_stats.video_count != current_stats.get("video_count")
        ):
            stats_data = UserStatsHistoryCreate(
                user_id=user_id,
                **current_stats
            )
            await self.create_stats(stats_data)
            return True
            
        return False