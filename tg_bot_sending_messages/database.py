# import aiosqlite
# import os

# # from loguru import logger
# from configuration.logger_setup import logger


# class DatabaseInitializer:
#     def __init__(self, db_name="bot_data.db"):
#         # Определение текущего каталога
#         self.current_directory = os.getcwd()
#         # Определение пути к директории базы данных
#         self.database_path = os.path.join(self.current_directory, "database")
#         # Создание директории, если она не существует
#         os.makedirs(self.database_path, exist_ok=True)
#         # Определение полного пути к файлу базы данных
#         self.database_file = os.path.join(self.database_path, db_name)

#     async def init_db(self):
#         # Подключение к базе данных
#         async with aiosqlite.connect(self.database_file) as db:
#             # Создание таблицы groups, если она не существует
#             await db.execute(
#                 """CREATE TABLE IF NOT EXISTS groups (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     group_id INTEGER UNIQUE)"""
#             )
#             # Создание таблицы sessions, если она не существует
#             await db.execute(
#                 """CREATE TABLE IF NOT EXISTS sessions (
#                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                                 session_name TEXT UNIQUE NOT NULL)"""
#             )
#             # Создание таблицы accounts, если она не существует
#             await db.execute(
#                 """CREATE TABLE IF NOT EXISTS accounts (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 api_id TEXT NOT NULL,
#                 api_hash TEXT NOT NULL,
#                 phone_number TEXT UNIQUE NOT NULL)"""
#             )
#             await db.execute(
#                 """CREATE TABLE IF NOT EXISTS link_groups(
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     link_group INTEGER UNIQUE)"""
#             )
#             # Сохранение изменений в базе данных
#             await db.commit()

#     async def add_group(self, group_id):
#         async with aiosqlite.connect(self.database_file) as db:
#             try:
#                 logger.debug(f"Проверка наличия группы с ID {group_id} в базе данных")
#                 async with db.execute(
#                     "SELECT 1 FROM groups WHERE group_id = ?", (group_id,)
#                 ) as cursor:
#                     exists = await cursor.fetchone()
#                 if exists:
#                     logger.info(f"Группа с ID {group_id} уже существует")
#                     return f"Группа с ID {group_id} уже существует."
#                 else:
#                     logger.debug(f"Добавление группы с ID {group_id}")
#                     await db.execute(
#                         """INSERT INTO groups (group_id) VALUES (?)""",
#                         (group_id,),
#                     )
#                     await db.commit()
#                     logger.info(f"Группа {group_id} добавлена в базу данных")
#                     return f"Группа с ID {group_id} добавлена."
#             except Exception as e:
#                 logger.error(f"Ошибка при добавлении группы {group_id}: {e}")
#                 return f"Ошибка при добавлении группы с ID {group_id}: {e}"

#     async def get_groups(self):
#         async with aiosqlite.connect(self.database_file) as db:
#             async with db.execute("SELECT group_id FROM groups") as cursor:
#                 groups = await cursor.fetchall()
#                 # Преобразование списка кортежей в плоский список ID
#                 group_ids = [group_id[0] for group_id in groups]
#                 logger.debug(f"Получен список групп: {group_ids}")
#                 return group_ids


import aiomysql
import asyncio
from configuration.config import DB_CONFIG
from loguru import logger
import os


class DatabaseInitializer:
    def __init__(self):
        pass

    async def create_pool(self):
        self.pool = await aiomysql.create_pool(
            host=DB_CONFIG["host"],
            port=3306,
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            db=DB_CONFIG["db"],
            charset="utf8mb4",
            autocommit=True,
        )

    async def init_db(self):
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
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

    async def add_group(self, group_id):
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                try:
                    logger.debug(
                        f"Проверка наличия группы с ID {group_id} в базе данных"
                    )
                    await cursor.execute(
                        "SELECT 1 FROM groups_for_messages WHERE group_id = %s",
                        (group_id,),
                    )
                    exists = await cursor.fetchone()
                    if exists:
                        logger.info(f"Группа с ID {group_id} уже существует")
                        return f"Группа с ID {group_id} уже существует."
                    else:
                        logger.debug(f"Добавление группы с ID {group_id}")
                        await cursor.execute(
                            "INSERT INTO groups_for_messages (group_id) VALUES (%s)",
                            (group_id,),
                        )
                        logger.info(f"Группа {group_id} добавлена в базу данных")
                        return f"Группа с ID {group_id} добавлена."
                except Exception as e:
                    logger.error(f"Ошибка при добавлении группы {group_id}: {e}")
                    return f"Ошибка при добавлении группы с ID {group_id}: {e}"

    async def get_groups(self):
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT group_id FROM groups_for_messages")
                groups = await cursor.fetchall()
                group_ids = [group_id[0] for group_id in groups]
                logger.debug(f"Получен список групп: {group_ids}")
                return group_ids
