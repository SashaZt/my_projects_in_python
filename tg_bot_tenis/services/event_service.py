# services/event_service.py
from typing import List, Optional
from datetime import datetime
from database.connection import get_db
from database.models import Event
from config.logger import logger
from config import get_weekday_from_date

class EventService:
    @staticmethod
    async def create_event(title: str, event_date: str, event_time: str, 
                        location: str, created_by: int) -> Event:
        """Создать новое событие"""
        
        
        weekday = get_weekday_from_date(event_date)
        
        async with get_db() as db:
            cursor = await db.execute(
                """INSERT INTO events (title, event_date, event_time, location, created_by, weekday) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (title, event_date, event_time, location, created_by, weekday)
            )
            await db.commit()
            event_id = cursor.lastrowid
            
            logger.info(f"✅ Событие создано: ID {event_id}, день недели: {weekday}")
            
            return Event(
                id=event_id,
                title=title,
                event_date=event_date,
                event_time=event_time,
                location=location,
                created_by=created_by,
                weekday=weekday
            )
    
    @staticmethod
    async def get_active_events() -> List[Event]:
        """Получить все активные события"""
        async with get_db() as db:
            async with db.execute(
                "SELECT * FROM events WHERE is_active = TRUE ORDER BY event_date, event_time"
            ) as cursor:
                rows = await cursor.fetchall()
                return [Event(*row) for row in rows]
    
    @staticmethod
    async def get_event_by_id(event_id: int) -> Optional[Event]:
        """Получить событие по ID"""
        async with get_db() as db:
            async with db.execute(
                "SELECT * FROM events WHERE id = ?", (event_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Event(
                        id=row[0], 
                        title=row[1], 
                        event_date=row[2], 
                        event_time=row[3],
                        location=row[4], 
                        max_participants=row[5], 
                        price=row[6],
                        created_by=row[7], 
                        is_active=row[8], 
                        created_at=row[9],
                        group_message_id=row[10] if len(row) > 10 else None,
                        weekday=row[11] if len(row) > 11 else 0
                    )
                return None
    @staticmethod
    async def deactivate_event(event_id: int) -> bool:
        """Деактивировать событие"""
        async with get_db() as db:
            await db.execute(
                "UPDATE events SET is_active = FALSE WHERE id = ?", (event_id,)
            )
            await db.commit()
            return True
    
    @staticmethod
    async def get_events_by_creator(creator_id: int) -> List[Event]:
        """Получить события созданные конкретным пользователем"""
        async with get_db() as db:
            async with db.execute(
                "SELECT * FROM events WHERE created_by = ? ORDER BY event_date, event_time",
                (creator_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Event(*row) for row in rows]
    @staticmethod
    async def update_group_message_id(event_id: int, group_message_id: int):
        """Обновить ID сообщения в группе"""
        async with get_db() as db:
            await db.execute(
                "UPDATE events SET group_message_id = ? WHERE id = ?",
                (group_message_id, event_id)
            )
            await db.commit()
            logger.info(f"✅ Обновлен group_message_id для события {event_id}: {group_message_id}")
