import aiosqlite
import os

# from loguru import logger
from configuration.logger_setup import logger


class DatabaseInitializer:
    def __init__(self, db_name="bot_data.db"):
        # Определение текущего каталога
        self.current_directory = os.getcwd()
        # Определение пути к директории базы данных
        self.database_path = os.path.join(self.current_directory, "database")
        # Создание директории, если она не существует
        os.makedirs(self.database_path, exist_ok=True)
        # Определение полного пути к файлу базы данных
        self.database_file = os.path.join(self.database_path, db_name)

    async def init_db(self):
        # Подключение к базе данных
        async with aiosqlite.connect(self.database_file) as db:
            # Создание таблицы groups, если она не существует
            await db.execute(
                """CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER UNIQUE,
                    group_name TEXT UNIQUE
                )"""
            )
            # Создание таблицы sessions, если она не существует
            await db.execute(
                """CREATE TABLE IF NOT EXISTS sessions (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                session_name TEXT UNIQUE NOT NULL)"""
            )
            # Создание таблицы accounts, если она не существует
            await db.execute(
                """CREATE TABLE IF NOT EXISTS accounts (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                account_name TEXT UNIQUE NOT NULL,
                                api_id TEXT NOT NULL,
                                api_hash TEXT NOT NULL)"""
            )
            # Сохранение изменений в базе данных
            await db.commit()

    async def add_group(self, group_id, group_name):
        async with aiosqlite.connect(self.database_file) as db:
            try:
                logger.debug(
                    f"Проверка наличия группы с ID {group_id} и именем {group_name} в базе данных"
                )
                async with db.execute(
                    "SELECT 1 FROM groups WHERE group_id = ? OR group_name = ?",
                    (group_id, group_name),
                ) as cursor:
                    exists = await cursor.fetchone()
                if exists:
                    logger.info(
                        f"Группа с ID {group_id} или именем {group_name} уже существует"
                    )
                    return f"Группа с ID {group_id} или именем {group_name} уже существует."
                else:
                    logger.debug(
                        f"Добавление группы с ID {group_id} и именем {group_name}"
                    )
                    await db.execute(
                        """INSERT INTO groups (group_id, group_name) VALUES (?, ?)""",
                        (group_id, group_name),
                    )
                    await db.commit()
                    logger.info(
                        f"Группа {group_id}.{group_name} добавлена в базу данных"
                    )
                    return f"Группа '{group_id}.{group_name}' добавлена."
            except Exception as e:
                logger.error(
                    f"Ошибка при добавлении группы {group_id}.{group_name}: {e}"
                )
                return f"Ошибка при добавлении группы '{group_id}.{group_name}': {e}"

    async def get_groups(self):
        async with aiosqlite.connect(self.database_file) as db:
            async with db.execute("SELECT group_id, group_name FROM groups") as cursor:
                groups = await cursor.fetchall()
                logger.debug(f"Получен список групп: {groups}")
                return groups
