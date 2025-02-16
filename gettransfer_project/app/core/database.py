# /app/core/database.py
from core.config import DATABASE_URL  # Импорт строки подключения к базе данных.
from core.base import Base  # Импорт базового класса для моделей.
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

# Создание асинхронного движка базы данных.
try:
    engine = create_async_engine(DATABASE_URL, echo=True)
except Exception as e:
    raise RuntimeError(f"Failed to create engine: {e}")

# Создание фабрики асинхронных сессий.
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Асинхронная функция для получения сессии базы данных.
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
