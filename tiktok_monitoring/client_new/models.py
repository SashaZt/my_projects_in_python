# client/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class Streamer:
    """Модель данных стримера"""
    id: int
    name: str
    unique_id: str  # name с префиксом @
    user_id: int = 0
    cluster: str = "AGENCY"
    cluster_id: int = None
    status: str = "Запущен"  # Запущен или Остановлен
    check_online: int = 30  # Интервал проверки в секундах
    start_date: datetime = None
    last_activity: datetime = None
    
    @classmethod
    def from_db(cls, row: Dict[str, Any]) -> 'Streamer':
        """Создание объекта из строки БД"""
        return cls(
            id=row.get('id', 0),
            name=row.get('name', ''),
            unique_id=row.get('name', '') if row.get('name', '').startswith('@') else f"@{row.get('name', '')}",
            user_id=row.get('user_id', 0),
            cluster=row.get('cluster', 'AGENCY'),
            cluster_id=row.get('cluster_id'),
            status=row.get('status', 'Запущен'),
            check_online=row.get('check_online', 30),
            start_date=row.get('start_date'),
            last_activity=row.get('last_activity')
        )
    
    @property
    def is_active(self) -> bool:
        """Активен ли стример"""
        return self.status == 'Запущен'


@dataclass
class Cluster:
    """Модель данных кластера стримеров"""
    id: int
    name: str
    created_at: datetime = None
    
    @classmethod
    def from_db(cls, row: Dict[str, Any]) -> 'Cluster':
        """Создание объекта из строки БД"""
        return cls(
            id=row.get('id', 0),
            name=row.get('name', ''),
            created_at=row.get('created_at')
        )


@dataclass
class Gift:
    """Модель данных подарка"""
    user_id: str  # ID пользователя-донатера
    unique_id: str  # Имя пользователя-донатера
    follow_role: int  # 0=нет, 1=фолловер, 2=друг
    is_new_gifter: bool  # Первый подарок от этого пользователя
    diamond_count: int  # Стоимость подарка в диамантах
    gift_name: str  # Название подарка
    gift_count: int  # Количество подарков в стаке
    receiver_user_id: str  # ID стримера-получателя
    receiver_unique_id: str  # Имя стримера-получателя
    cluster: str  # Кластер стримера
    event_time: datetime  # Время события
    top_gifter_rank: Optional[int] = None  # Ранг донатера
    id: Optional[int] = None  # ID в базе данных
    
    @property
    def total_diamonds(self) -> int:
        """Общая стоимость подарка с учетом количества"""
        return self.diamond_count * self.gift_count
    
    @property
    def dollars(self) -> float:
        """Стоимость подарка в долларах"""
        return self.total_diamonds / 200
    
    @classmethod
    def from_event(cls, event: Dict[str, Any], unique_id: str, cluster: str) -> 'Gift':
        """Создание объекта из события TikTokLive"""
        event_time = datetime.now() if not event.get('event_time') else event['event_time']
        
        return cls(
            user_id=event.get('user_id', '0'),
            unique_id=event.get('unique_id', 'unknown_user'),
            follow_role=event.get('follow_role', 0),
            is_new_gifter=event.get('is_new_gifter', False),
            top_gifter_rank=event.get('top_gifter_rank'),
            diamond_count=event.get('diamond_count', 0),
            gift_name=event.get('gift_name', 'Unknown Gift'),
            gift_count=event.get('gift_count', 1),
            receiver_user_id=event.get('receiver_user_id', unique_id.replace('@', '')),
            receiver_unique_id=unique_id,
            cluster=cluster,
            event_time=event_time
        )
    
    @classmethod
    def from_db(cls, row: Dict[str, Any]) -> 'Gift':
        """Создание объекта из строки БД"""
        return cls(
            id=row.get('id'),
            user_id=row.get('user_id', '0'),
            unique_id=row.get('unique_id', ''),
            follow_role=row.get('follow_role', 0),
            is_new_gifter=row.get('is_new_gifter', False),
            top_gifter_rank=row.get('top_gifter_rank'),
            diamond_count=row.get('diamond_count', 0),
            gift_name=row.get('gift_name', ''),
            gift_count=row.get('gift_count', 1),
            receiver_user_id=row.get('receiver_user_id', ''),
            receiver_unique_id=row.get('receiver_unique_id', ''),
            cluster=row.get('cluster', 'AGENCY'),
            event_time=row.get('event_time', datetime.now())
        )


@dataclass
class Gifter:
    """Модель данных донатера"""
    id: int
    user_id: str
    unique_id: str
    total_diamond_count: int = 0
    total_gift_count: int = 0
    first_gift_date: Optional[datetime] = None
    last_gift_date: Optional[datetime] = None
    first_receiver_user_id: Optional[str] = None
    last_update: Optional[datetime] = None
    
    @classmethod
    def from_db(cls, row: Dict[str, Any]) -> 'Gifter':
        """Создание объекта из строки БД"""
        return cls(
            id=row.get('id', 0),
            user_id=row.get('user_id', ''),
            unique_id=row.get('unique_id', ''),
            total_diamond_count=row.get('total_diamond_count', 0),
            total_gift_count=row.get('total_gift_count', 0),
            first_gift_date=row.get('first_gift_date'),
            last_gift_date=row.get('last_gift_date'),
            first_receiver_user_id=row.get('first_receiver_user_id'),
            last_update=row.get('last_update')
        )


@dataclass
class DashboardStats:
    """Модель данных статистики для дашборда"""
    total_gifts_today: int = 0
    total_gifts_yesterday: int = 0
    total_diamonds_today: int = 0
    total_diamonds_yesterday: int = 0
    total_dollars_today: float = 0.0
    total_dollars_yesterday: float = 0.0
    total_dollars_this_week: float = 0.0
    total_dollars_last_week: float = 0.0
    total_dollars_this_month: float = 0.0
    total_dollars_last_month: float = 0.0
    active_streamers_count: int = 0
    total_streamers_count: int = 0
    total_unique_gifters: int = 0
    unique_gifters_this_week: int = 0
    unique_gifters_last_week: int = 0
    
    @property
    def gifts_today_percent(self) -> str:
        """Процентное изменение количества подарков сегодня по сравнению со вчера"""
        if self.total_gifts_yesterday == 0:
            return "N/A"
        
        percent = ((self.total_gifts_today - self.total_gifts_yesterday) / self.total_gifts_yesterday) * 100
        if percent > 0:
            return f"↑ {percent:.2f}%"
        elif percent < 0:
            return f"↓ {abs(percent):.2f}%"
        else:
            return "↔ 0.00%"
    
    @property
    def diamonds_today_percent(self) -> str:
        """Процентное изменение количества диамантов сегодня по сравнению со вчера"""
        if self.total_diamonds_yesterday == 0:
            return "N/A"
        
        percent = ((self.total_diamonds_today - self.total_diamonds_yesterday) / self.total_diamonds_yesterday) * 100
        if percent > 0:
            return f"↑ {percent:.2f}%"
        elif percent < 0:
            return f"↓ {abs(percent):.2f}%"
        else:
            return "↔ 0.00%"
    
    @property
    def dollars_today_percent(self) -> str:
        """Процентное изменение суммы в долларах сегодня по сравнению со вчера"""
        if self.total_dollars_yesterday == 0:
            return "N/A"
        
        percent = ((self.total_dollars_today - self.total_dollars_yesterday) / self.total_dollars_yesterday) * 100
        if percent > 0:
            return f"↑ {percent:.2f}%"
        elif percent < 0:
            return f"↓ {abs(percent):.2f}%"
        else:
            return "↔ 0.00%"
    
    @property
    def dollars_week_percent(self) -> str:
        """Процентное изменение суммы в долларах за неделю по сравнению с прошлой неделей"""
        if self.total_dollars_last_week == 0:
            return "N/A"
        
        percent = ((self.total_dollars_this_week - self.total_dollars_last_week) / self.total_dollars_last_week) * 100
        if percent > 0:
            return f"↑ {percent:.2f}%"
        elif percent < 0:
            return f"↓ {abs(percent):.2f}%"
        else:
            return "↔ 0.00%"
    
    @property
    def dollars_month_percent(self) -> str:
        """Процентное изменение суммы в долларах за месяц по сравнению с прошлым месяцем"""
        if self.total_dollars_last_month == 0:
            return "N/A"
        
        percent = ((self.total_dollars_this_month - self.total_dollars_last_month) / self.total_dollars_last_month) * 100
        if percent > 0:
            return f"↑ {percent:.2f}%"
        elif percent < 0:
            return f"↓ {abs(percent):.2f}%"
        else:
            return "↔ 0.00%"
    
    @property
    def gifters_week_percent(self) -> str:
        """Процентное изменение количества уникальных донатеров за неделю"""
        if self.unique_gifters_last_week == 0:
            return "N/A"
        
        percent = ((self.unique_gifters_this_week - self.unique_gifters_last_week) / self.unique_gifters_last_week) * 100
        if percent > 0:
            return f"↑ {percent:.2f}%"
        elif percent < 0:
            return f"↓ {abs(percent):.2f}%"
        else:
            return "↔ 0.00%"
    
    @classmethod
    def from_db(cls, row: Dict[str, Any]) -> 'DashboardStats':
        """Создание объекта из строки БД"""
        return cls(
            total_gifts_today=row.get('total_gifts_today', 0),
            total_gifts_yesterday=row.get('total_gifts_yesterday', 0),
            total_diamonds_today=row.get('total_diamonds_today', 0),
            total_diamonds_yesterday=row.get('total_diamonds_yesterday', 0),
            total_dollars_today=row.get('total_dollars_today', 0.0),
            total_dollars_yesterday=row.get('total_dollars_yesterday', 0.0),
            total_dollars_this_week=row.get('total_dollars_this_week', 0.0),
            total_dollars_last_week=row.get('total_dollars_last_week', 0.0),
            total_dollars_this_month=row.get('total_dollars_this_month', 0.0),
            total_dollars_last_month=row.get('total_dollars_last_month', 0.0),
            active_streamers_count=row.get('active_streamers_count', 0),
            total_streamers_count=row.get('total_streamers_count', 0),
            total_unique_gifters=row.get('total_unique_gifters', 0),
            unique_gifters_this_week=row.get('unique_gifters_this_week', 0),
            unique_gifters_last_week=row.get('unique_gifters_last_week', 0)
        )