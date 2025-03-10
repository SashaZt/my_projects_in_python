# app/core/db.py
import os
from app.core.config import settings
from app.core.logger import logger

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Создаем асинхронный движок для подключения
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600,  # Обновление соединений через час
)

# Фабрика сессий для работы с БД
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Генератор для использования в зависимостях
async def get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Ошибка сессии БД: {str(e)}")
            await session.rollback()
            raise