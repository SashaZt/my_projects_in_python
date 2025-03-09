# src/db.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# создаёт асинхронный движок для подключения.
engine = create_async_engine(DATABASE_URL, echo=True)
# фабрика сессий для работы с БД.
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# генератор для использования в зависимостях (например, если будешь использовать FastAPI).
async def get_db():
    
    async with async_session() as session:
        yield session