# app/core/db.py
from contextlib import asynccontextmanager

from app.core.database import async_session
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """Создает асинхронную сессию для работы с базой данных."""
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
