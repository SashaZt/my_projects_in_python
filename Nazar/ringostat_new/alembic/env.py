import os
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import async_engine_from_config, AsyncConnection
from sqlalchemy import pool
from app.models import *

from alembic import context
from app.core.base import Base
from app.core.config import DATABASE_URL

# Set metadata for Alembic
target_metadata = Base.metadata

# Alembic configuration
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Logging configuration
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
else:
    import logging

    logging.basicConfig(level=logging.INFO)

# Validate metadata
if not target_metadata:
    raise ValueError("Base.metadata is None. Check your SQLAlchemy models.")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection):
    """Actual migration runner"""
    context.configure(
        connection=connection, target_metadata=target_metadata, compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_migrations_online())
