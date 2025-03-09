from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.config import settings

# Создаем движок синхронно, без async/await
def get_engine() -> AsyncEngine:
    """
    Создает и возвращает асинхронный SQLAlchemy движок.
    """
    return create_async_engine(
        settings.db.async_database_url,
        echo=settings.DEBUG,  # Обратите внимание на исправление тут - settings.DEBUG вместо settings.db.DEBUG
        future=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # Пересоздавать соединения каждые 30 минут
    )

# Создаем глобальный экземпляр движка
engine = get_engine()