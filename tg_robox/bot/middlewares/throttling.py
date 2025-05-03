from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов от пользователей"""

    def __init__(self, rate_limit=0.5):
        self.rate_limit = rate_limit
        # Кэш для хранения последних запросов
        self.cache = TTLCache(maxsize=10000, ttl=self.rate_limit)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем ID пользователя
        user_id = event.from_user.id

        # Проверяем, есть ли пользователь в кэше
        if user_id in self.cache:
            # Если пользователь уже отправлял запрос недавно, игнорируем его
            return None

        # Добавляем пользователя в кэш
        self.cache[user_id] = True

        # Передаем управление следующему обработчику
        return await handler(event, data)
