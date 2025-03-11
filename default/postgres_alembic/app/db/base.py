# app/db/base.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Импортируем конфиг из корневой директории
from config import config  # Импорт синглтона ConfigManager
from app.models.base import Base  # Импорт базового класса моделей

# Получение параметров из конфигурации
database_config = config.get('database')

# URL базы данных (для использования в Alembic)
DATABASE_URL = config.get_database_url()

# Создание движка
engine = create_engine(
    DATABASE_URL,
    echo=database_config.get('echo_sql', False),
    pool_pre_ping=database_config.get('pool_pre_ping', True),
    pool_recycle=database_config.get('pool_recycle', 3600)
)

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()