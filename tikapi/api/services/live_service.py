# services/live_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from utils.time_utils import now_unix, datetime_to_unix, unix_to_datetime, date_to_unix
import datetime

from models.live import LiveStream, DailyLiveAnalytics
from schemas.live import LiveStreamCreate, DailyLiveAnalyticsCreate


class LiveService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_stream(self, stream_data: LiveStreamCreate) -> LiveStream:
        """Создание новой записи о прямой трансляции"""
        stream = LiveStream(
            user_id=stream_data.user_id,
            room_id=stream_data.room_id,
            start_time=stream_data.start_time,
            end_time=stream_data.end_time,
            diamonds=stream_data.diamonds,
            duration=stream_data.duration
        )
        
        self.db.add(stream)
        await self.db.commit()
        await self.db.refresh(stream)
        return stream
    
    async def get_user_streams(
        self, user_id: int, from_date: Optional[int] = None, to_date: Optional[int] = None
    ) -> List[LiveStream]:
        """Получение истории прямых трансляций пользователя за период"""
        query = select(LiveStream).where(LiveStream.user_id == user_id)

        
        if from_date:
            query = query.where(LiveStream.start_time >= from_date)
        if to_date:
            query = query.where(LiveStream.start_time <= to_date)
        
         # Сортировка по времени начала трансляции
        query = query.order_by(LiveStream.start_time.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_daily_analytics(self, analytics_data: DailyLiveAnalyticsCreate) -> DailyLiveAnalytics:
        """Добавление дневной аналитики по прямым трансляциям"""
        
        # Дополнительная проверка и преобразование даты
        if analytics_data.date is not None and not isinstance(analytics_data.date, int):
            try:
                from utils.time_utils import date_to_unix
                
                if isinstance(analytics_data.date, str):
                    # Преобразуем строку в дату
                    dt = datetime.strptime(analytics_data.date, "%Y-%m-%d").date()
                    analytics_data.date = date_to_unix(dt)
                elif isinstance(analytics_data.date, datetime):
                    analytics_data.date = date_to_unix(analytics_data.date.date())
                elif isinstance(analytics_data.date, date):
                    analytics_data.date = date_to_unix(analytics_data.date)
            except Exception as e:
                # Логирование ошибки
                print(f"Ошибка при преобразовании даты: {e}")
        
        # Проверяем, существует ли уже аналитика на этот день
        query = select(DailyLiveAnalytics).where(
            and_(
                DailyLiveAnalytics.user_id == analytics_data.user_id,
                DailyLiveAnalytics.date == analytics_data.date
            )
        )
        
        result = await self.db.execute(query)
        existing_analytics = result.scalars().first()
        
        if existing_analytics:
            # Обновляем существующую запись
            existing_analytics.diamonds_total = analytics_data.diamonds_total
            existing_analytics.live_duration_total = analytics_data.live_duration_total
            
            await self.db.commit()
            await self.db.refresh(existing_analytics)
            return existing_analytics
        else:
            # Создаем новую запись
            analytics = DailyLiveAnalytics(
                user_id=analytics_data.user_id,
                date=analytics_data.date,
                diamonds_total=analytics_data.diamonds_total,
                live_duration_total=analytics_data.live_duration_total
            )
            
            self.db.add(analytics)
            await self.db.commit()
            await self.db.refresh(analytics)
            return analytics
    
    async def get_user_analytics(
        self, user_id: int, from_date: Optional[int] = None, to_date: Optional[int] = None
    ) -> List[DailyLiveAnalytics]:
        """Получение дневной аналитики по прямым трансляциям пользователя за период"""
        query = select(DailyLiveAnalytics).where(DailyLiveAnalytics.user_id == user_id)
        
        if from_date:
            query = query.where(DailyLiveAnalytics.date >= from_date)
        if to_date:
            query = query.where(DailyLiveAnalytics.date <= to_date)
        
        # Сортировка по дате
        query = query.order_by(DailyLiveAnalytics.date.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def import_bulk_streams(self, user_id: int, streams_data: List[Dict[str, Any]]) -> List[LiveStream]:
        """Массовый импорт данных о прямых трансляциях для пользователя"""
        streams = []
        
        for stream_data in streams_data:
            # Проверяем, существует ли уже трансляция с таким room_id
            room_id = stream_data.get('room_id')
            if not room_id:
                continue
                
            query = select(LiveStream).where(
                and_(
                    LiveStream.user_id == user_id,
                    LiveStream.room_id == room_id
                )
            )
            
            result = await self.db.execute(query)
            existing_stream = result.scalars().first()
            
            if existing_stream:
                # Обновляем существующую трансляцию, если нужно
                if 'end_time' in stream_data and stream_data['end_time']:
                    existing_stream.end_time = stream_data['end_time']
                if 'diamonds' in stream_data:
                    existing_stream.diamonds = stream_data['diamonds']
                if 'duration' in stream_data:
                    existing_stream.duration = stream_data['duration']
                
                streams.append(existing_stream)
            else:
                # Создаем новую запись о трансляции
                # Теперь мы просто используем timestamp напрямую
                start_time = stream_data.get('start_time')          
                end_time = stream_data.get('end_time')
                
                stream = LiveStream(
                    user_id=user_id,
                    room_id=room_id,
                    start_time=start_time,
                    end_time=end_time,
                    diamonds=stream_data.get('diamonds'),
                    duration=stream_data.get('duration')
                )
                
                self.db.add(stream)
                streams.append(stream)
        
        # Сохраняем все изменения в базе данных
        await self.db.commit()
        
        # Обновляем объекты после коммита
        for stream in streams:
            await self.db.refresh(stream)
        
        # Также генерируем или обновляем дневную аналитику
        await self.generate_daily_analytics(user_id)
        
        return streams
    
    async def generate_daily_analytics(self, user_id: int) -> List[DailyLiveAnalytics]:
        """
        Генерирует или обновляет дневную аналитику на основе данных о трансляциях.
        Группирует данные по дням, преобразуя Unix timestamp в дату.
        """
        # Запрос для получения всех трансляций пользователя
        query = select(LiveStream).where(LiveStream.user_id == user_id)
        result = await self.db.execute(query)
        streams = result.scalars().all()
        
        # Словарь для группировки по дням
        daily_data = {}
        
        # Обрабатываем каждую трансляцию
        for stream in streams:
            if not stream.start_time:
                continue
                
            # Преобразуем Unix timestamp в дату (без времени)
            # Для этого используем функцию из utils/time_utils.py
            day_timestamp = unix_to_datetime(stream.start_time)
            if not day_timestamp:
                continue
                
            # Получаем только дату (без времени) и конвертируем её обратно в timestamp начала дня
            day_date = day_timestamp.date()
            day_start_timestamp = date_to_unix(day_date)
            
            # Инициализируем данные для дня, если ещё нет
            if day_start_timestamp not in daily_data:
                daily_data[day_start_timestamp] = {
                    'diamonds': 0,
                    'duration': 0
                }
                
            # Суммируем данные
            if stream.diamonds:
                daily_data[day_start_timestamp]['diamonds'] += stream.diamonds
            if stream.duration:
                daily_data[day_start_timestamp]['duration'] += stream.duration
        
        # Создаем или обновляем дневную аналитику
        analytics_list = []
        
        for day_timestamp, data in daily_data.items():
            analytics_data = DailyLiveAnalyticsCreate(
                user_id=user_id,
                date=day_timestamp,
                diamonds_total=data['diamonds'],
                live_duration_total=data['duration']
            )
            
            analytics = await self.create_daily_analytics(analytics_data)
            analytics_list.append(analytics)
                
        return analytics_list