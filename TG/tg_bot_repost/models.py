import os
from datetime import datetime, timezone

from config import DB_NAME
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 🔹 Настройка подключения к БД
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.abspath(DB_NAME)}"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# 🔹 Определение базы данных
class Base(DeclarativeBase):
    pass


class RepostMessage(Base):
    __tablename__ = "repost_messages"

    __table_args__ = (
        Index("idx_category_repost", "category", "repost"),
        UniqueConstraint("message_id", "category", name="uix_message_category"),
    )

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    repost = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reposted_at = Column(DateTime, nullable=True)


# 🔹 Создание таблицы (при первом запуске)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
