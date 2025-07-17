# services/booking_service.py
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from database.connection import get_db
from database.models import Booking
from config import CANCEL_HOURS_LIMIT

class BookingService:
    @staticmethod
    async def register_user(event_id: int, user_id: int) -> Tuple[bool, str]:
        """Записать пользователя на событие"""
        async with get_db() as db:
            # Проверяем не записан ли уже
            async with db.execute(
                "SELECT * FROM bookings WHERE event_id = ? AND user_id = ? AND status = 'registered'",
                (event_id, user_id)
            ) as cursor:
                existing = await cursor.fetchone()
                
            if existing:
                return False, "Вы уже записаны на это событие"
            
            # Проверяем количество свободных мест
            async with db.execute(
                """SELECT COUNT(*) FROM bookings 
                   WHERE event_id = ? AND status = 'registered'""",
                (event_id,)
            ) as cursor:
                count = await cursor.fetchone()
                current_bookings = count[0] if count else 0
            
            if current_bookings >= 4:  # MAX_PARTICIPANTS
                return False, "Нет свободных мест"
            
            # Записываем пользователя
            await db.execute(
                """INSERT OR REPLACE INTO bookings (event_id, user_id, status) 
                   VALUES (?, ?, 'registered')""",
                (event_id, user_id)
            )
            await db.commit()
            
            return True, "Вы успешно записались на событие"
    
    @staticmethod
    async def cancel_booking(event_id: int, user_id: int) -> Tuple[bool, str]:
        """Отменить запись на событие"""
        async with get_db() as db:
            # Получаем информацию о событии
            async with db.execute(
                "SELECT event_date, event_time FROM events WHERE id = ?", (event_id,)
            ) as cursor:
                event_info = await cursor.fetchone()
                
            if not event_info:
                return False, "Событие не найдено"
            
            # Проверяем временное ограничение
            event_date, event_time = event_info
            event_datetime = datetime.strptime(f"{event_date} {event_time}", "%d.%m.%Y %H:%M")
            now = datetime.now()
            time_diff = event_datetime - now
            
            if time_diff.total_seconds() < CANCEL_HOURS_LIMIT * 3600:
                return False, f"Отмена возможна не позднее чем за {CANCEL_HOURS_LIMIT} часов до события"
            
            # Проверяем есть ли активная запись
            async with db.execute(
                "SELECT * FROM bookings WHERE event_id = ? AND user_id = ? AND status = 'registered'",
                (event_id, user_id)
            ) as cursor:
                booking = await cursor.fetchone()
                
            if not booking:
                return False, "Вы не записаны на это событие"
            
            # Отменяем запись
            await db.execute(
                """UPDATE bookings SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP 
                   WHERE event_id = ? AND user_id = ?""",
                (event_id, user_id)
            )
            await db.commit()
            
            return True, "Запись отменена"
    
    @staticmethod
    async def get_event_bookings(event_id: int) -> List[Booking]:
        """Получить все записи на событие"""
        async with get_db() as db:
            async with db.execute(
                """SELECT * FROM bookings 
                   WHERE event_id = ? AND status = 'registered'
                   ORDER BY created_at""",
                (event_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Booking(*row) for row in rows]
    
    @staticmethod
    async def get_user_bookings(user_id: int) -> List[Tuple[Booking, str, str, str]]:
        """Получить записи пользователя с информацией о событиях"""
        async with get_db() as db:
            async with db.execute(
                """SELECT b.*, e.title, e.event_date, e.event_time 
                   FROM bookings b
                   JOIN events e ON b.event_id = e.id
                   WHERE b.user_id = ? AND b.status = 'registered'
                   ORDER BY e.event_date, e.event_time""",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [(Booking(*row[:6]), row[6], row[7], row[8]) for row in rows]
    
    @staticmethod
    async def get_booking_count(event_id: int) -> int:
        """Получить количество активных записей на событие"""
        from config.logger import logger
        
        async with get_db() as db:
            async with db.execute(
                "SELECT COUNT(*) FROM bookings WHERE event_id = ? AND status = 'registered'",
                (event_id,)
            ) as cursor:
                result = await cursor.fetchone()
                count = result[0] if result else 0
                
                logger.debug(f"📊 Событие {event_id}: найдено {count} активных записей")
                return count