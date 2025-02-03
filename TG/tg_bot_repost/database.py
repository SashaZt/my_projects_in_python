import os

from config import DB_NAME, logger
from models import Base, RepostMessage, async_session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

# 🔹 Настройка подключения к БД
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.abspath(DB_NAME)}"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# 🔹 Функция для инициализации БД
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 🔹 Функция для получения сообщений, которые еще не пересланы
async def fetch_pending_messages(category: str, limit: int):
    async with async_session() as session:
        result = await session.execute(
            select(RepostMessage.message_id)
            .where(RepostMessage.category == category, RepostMessage.repost == False)
            .limit(limit)
        )
        messages = result.scalars().all()
        logger.info(f"📌 Найдено {len(messages)} сообщений для пересылки ({category})")
        return messages
