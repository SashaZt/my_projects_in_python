import os
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import (
    async_engine_from_config,
    AsyncConnection,
)  # Для работы с асинхронным движком.
from sqlalchemy import pool  # Настройка пула подключений.
from app.models import *  # Импорт всех моделей для получения метаданных.

from alembic import context  # Основной модуль Alembic для работы с миграциями.
from app.core.base import Base  # Общий Base для всех моделей.
from app.core.config import DATABASE_URL  # URL для подключения к базе данных.


# Set metadata for Alembic
target_metadata = (
    Base.metadata
)  # Метаданные моделей для автоматической генерации миграций.

# Alembic configuration
config = context.config
config.set_main_option(
    "sqlalchemy.url", DATABASE_URL
)  # Устанавливаем URL для подключения к базе данных.

# Logging configuration
if config.config_file_name is not None:
    fileConfig(config.config_file_name)  # Настройки логирования из файла конфигурации.
else:
    import logging

    logging.basicConfig(level=logging.INFO)  # Базовая настройка логирования.


# Validate metadata
if not target_metadata:
    raise ValueError("Базовые метаданные — None. Проверьте свои модели SQLAlchemy.")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,  # URL для подключения к базе данных.
        target_metadata=target_metadata,  # Метаданные для автоматической генерации миграций.
        literal_binds=True,  # Генерация миграций с прямыми значениями вместо параметров.
        dialect_opts={"paramstyle": "named"},  # Формат параметров для диалекта базы.
    )
    with context.begin_transaction():
        context.run_migrations()  # Выполнение миграций в офлайн-режиме.


async def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = async_engine_from_config(
        config.get_section(
            config.config_ini_section
        ),  # Конфигурация из файла alembic.ini.
        prefix="sqlalchemy.",  # Префикс для настроек SQLAlchemy.
        poolclass=pool.NullPool,  # Использование пула подключений.
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            do_run_migrations
        )  # Выполнение миграций через подключение.


def do_run_migrations(connection):
    """Actual migration runner"""
    context.configure(
        connection=connection,  # Подключение к базе данных.
        target_metadata=target_metadata,  # Метаданные моделей.
        compare_type=True,  # Проверка на изменение типов данных.
    )

    with context.begin_transaction():
        context.run_migrations()  # Выполнение миграций.


if context.is_offline_mode():
    run_migrations_offline()  # Запуск офлайн-режима, если включён.
else:
    import asyncio

    asyncio.run(run_migrations_online())  # Запуск онлайн-режима.
