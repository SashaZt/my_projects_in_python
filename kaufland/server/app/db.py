# app/db.py
import logging
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Загружаем переменные окружения из .env файла, если он существует
load_dotenv()

# Получаем URL подключения к базе данных из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")

# Логируем для отладки (без персональных данных)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Попытка подключения к базе данных (URL скрыт для безопасности)")

if not DATABASE_URL:
    logger.error("DATABASE_URL не установлен. Проверьте переменные окружения.")
    # Используем фиктивный URL для предотвращения ошибки при импорте
    # Реальное соединение не будет установлено, но приложение загрузится
    DATABASE_URL = (
        "postgresql+asyncpg://postgres_user:postgres_password@localhost/kaufland"
    )

# Создаем асинхронный движок для подключения
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600,  # Обновление соединений через час
)

# Фабрика сессий для работы с БД
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Генератор для использования в зависимостях
async def get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Ошибка сессии БД: {str(e)}")
            await session.rollback()
            raise
