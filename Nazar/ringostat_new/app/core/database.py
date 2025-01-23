from app.core.config import DATABASE_URL
from app.core.base import Base  # Import Base from the new base.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Создание движка
try:
    engine = create_async_engine(DATABASE_URL, echo=True)
except Exception as e:
    raise RuntimeError(f"Failed to create engine: {e}")

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Функция для получения сессии
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
