import aiomysql
import asyncio
from configuration.config import DB_CONFIG
from loguru import logger
import os


class DatabaseInitializer:
    def __init__(self):
        self.pool = None

    async def create_pool(self):
        logger.info("Создание пула соединений с базой данных")
        self.pool = await aiomysql.create_pool(
            host=DB_CONFIG["host"],
            port=3306,
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            db=DB_CONFIG["db"],
            charset="utf8mb4",
            autocommit=True,
        )
        logger.info("Пул соединений успешно создан")

    async def init_db(self):
        logger.info("Инициализация базы данных")
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                try:
                    await cursor.execute(
                        """CREATE TABLE IF NOT EXISTS groups_for_messages (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            group_id BIGINT UNIQUE)"""
                    )
                    await cursor.execute(
                        """CREATE TABLE IF NOT EXISTS sessions_for_messages (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            session_name VARCHAR(255) UNIQUE NOT NULL)"""
                    )
                    await cursor.execute(
                        """CREATE TABLE IF NOT EXISTS accounts_for_messages (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            api_id VARCHAR(255) NOT NULL,
                            api_hash VARCHAR(255) NOT NULL,
                            phone_number VARCHAR(20) UNIQUE NOT NULL)"""
                    )
                    logger.info("Таблицы созданы или уже существуют")
                except Exception as e:
                    logger.error(f"Ошибка при инициализации базы данных: {e}")

    async def add_groups(self, group_ids):
        """Добавление нескольких групп в базу данных."""
        logger.debug(f"Добавление групп: {group_ids}")
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                try:
                    query = (
                        "INSERT IGNORE INTO groups_for_messages (group_id) VALUES (%s)"
                    )
                    await cursor.executemany(
                        query, [(group_id,) for group_id in group_ids]
                    )
                    logger.info(f"Добавлены группы: {group_ids}")
                except Exception as e:
                    logger.error(f"Ошибка при добавлении групп: {e}")

    async def get_groups(self):
        logger.debug("Получение списка групп из базы данных")
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                try:
                    logger.debug("Выполнение запроса для получения group_id")
                    await cursor.execute("SELECT group_id FROM groups_for_messages")
                    groups = await cursor.fetchall()
                    group_ids = [group_id[0] for group_id in groups]
                    if not group_ids:
                        logger.warning("Список group_ids пустой")
                    else:
                        logger.debug(f"Получен список групп: {group_ids}")
                    return group_ids
                except Exception as e:
                    logger.error(f"Ошибка при получении списка групп: {e}")
                    return []
