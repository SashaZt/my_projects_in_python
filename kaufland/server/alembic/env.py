# alembic/env.py
import os
from logging.config import fileConfig

from alembic import context
from app.models import Base  # Изменено с src.models на app.models
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# Загружаем переменные окружения из .env
load_dotenv()

# Конфигурация Alembic
config = context.config

# Настройка логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные моделей
target_metadata = Base.metadata

# Получаем URL базы данных из .env и заменяем asyncpg на psycopg2 для синхронного подключения
DATABASE_URL = os.getenv("DATABASE_URL").replace(
    "postgresql+asyncpg", "postgresql+psycopg2"
)


def run_migrations_offline():
    """Запуск миграций в оффлайн-режиме"""
    url = config.get_main_option("sqlalchemy.url", DATABASE_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Запуск миграций в онлайн-режиме"""
    # Создаём синхронный движок для миграций
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        url=DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
