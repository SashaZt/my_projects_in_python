from app.core.config import DATABASE_URL  # Импорт строки подключения к базе данных.
from app.core.base import Base  # Импорт базового класса для моделей.
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)  # Асинхронные компоненты SQLAlchemy.
from sqlalchemy.orm import sessionmaker  # Для создания фабрики сессий.

# Создание асинхронного движка базы данных.
try:
    engine = create_async_engine(DATABASE_URL, echo=True)
except Exception as e:
    # В случае ошибки при создании движка, выбрасываем исключение с описанием.
    raise RuntimeError(f"Failed to create engine: {e}")

# Создание фабрики асинхронных сессий.
# `expire_on_commit=False` означает, что данные будут оставаться доступными после коммита.
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Асинхронная функция для получения сессии базы данных.
# Это позволяет использовать `AsyncSession` в виде зависимости через FastAPI.
async def get_session() -> AsyncSession:
    async with async_session() as session:
        # Используем `yield` для работы с асинхронным контекстом.
        yield session
