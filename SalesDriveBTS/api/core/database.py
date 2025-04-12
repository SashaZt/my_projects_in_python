from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from typing import AsyncGenerator

from core.config import settings
from core.logger import logger

# Создаем базовый класс моделей
class CustomBase:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

# Базовый класс для всех моделей
Base = declarative_base(cls=CustomBase)

# Создаем async engine для SQLAlchemy
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Создаем фабрику сессий
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость для получения сессии базы данных.
    
    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy
    """
    async with async_session() as session:
        try:
            logger.debug("Создана новая сессия базы данных")
            yield session
        finally:
            logger.debug("Сессия базы данных закрыта")
            await session.close()

# Функция для создания всех таблиц (для тестирования/разработки)
async def create_tables():
    """Создает все таблицы в базе данных."""
    logger.info("Создание таблиц в базе данных...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы созданы")

# Функция для удаления всех таблиц (для тестирования)
async def drop_tables():
    """Удаляет все таблицы из базы данных."""
    logger.warning("Удаление таблиц из базы данных!")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("Таблицы удалены")