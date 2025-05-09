# /app/websockets/database.py
import logging

import asyncpg
from config import settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.pool = None
        self.config = {
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "user": settings.POSTGRES_USER,
            "password": settings.POSTGRES_PASSWORD,
            "database": settings.POSTGRES_DB,
        }

    async def connect(self):
        """Подключение к базе данных PostgreSQL"""
        try:
            self.pool = await asyncpg.create_pool(**self.config)
            logger.info("Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            return False

    async def close(self):
        """Закрытие соединения с базой данных"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")

    async def fetch(self, query, *args):
        """Получение данных из базы"""
        if not self.pool:
            logger.error("Database not connected")
            return []

        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logger.error(f"Database fetch error: {e}")
            return []

    async def fetchrow(self, query, *args):
        """Получение одной строки из базы"""
        if not self.pool:
            logger.error("Database not connected")
            return None

        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            logger.error(f"Database fetchrow error: {e}")
            return None

    async def fetchval(self, query, *args):
        """Получение одного значения из базы"""
        if not self.pool:
            logger.error("Database not connected")
            return None

        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.error(f"Database fetchval error: {e}")
            return None

    async def execute(self, query, *args):
        """Выполнение SQL-запроса"""
        if not self.pool:
            logger.error("Database not connected")
            return None

        try:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return None

    async def executemany(self, query, args):
        """Пакетное выполнение запросов"""
        if not self.pool:
            logger.error("Database not connected")
            return None

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    return await conn.executemany(query, args)
        except Exception as e:
            logger.error(f"Database executemany error: {e}")
            return None


# Создаем экземпляр класса
db = Database()
