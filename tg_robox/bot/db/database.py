from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def create_async_engine(db_config):
    """
    Создает асинхронный движок SQLAlchemy для PostgreSQL
    """
    return _create_async_engine(
        db_config.get_connection_string(),
        echo=False,  # Установите True для вывода SQL-запросов в консоль
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
    )

def get_session_maker(engine):
    """
    Создает фабрику сессий для асинхронной работы с БД
    """
    return sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

async def init_models(engine):
    """
    Инициализирует модели в базе данных
    """
    async with engine.begin() as conn:
        # Только для разработки - раскомментируйте для сброса базы
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)