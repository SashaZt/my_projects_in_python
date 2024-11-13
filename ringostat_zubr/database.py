import asyncio
import os
from asyncio import TimeoutError, wait_for

import aiomysql
from configuration.logger_setup import logger
from dotenv import load_dotenv

# Указать путь к .env файлу
env_path = os.path.join(os.getcwd(), "configuration", ".env")

# Загрузить переменные из .env файла
load_dotenv(dotenv_path=env_path)

# Используйте переменные окружения для подключения к базе данных
user_db = os.getenv("USER_DB")
user_db_password = os.getenv("USER_DB_PASSWORD")
host_db = os.getenv("HOST_DB")
port_db = int(os.getenv("PORT_DB", 3306))
db_name = os.getenv("DB")
logger.info(user_db)


class DatabaseInitializer:
    def __init__(self):
        self.pool = None  # Инициализация атрибута пула соединений

    async def create_database(self):
        """Создание базы данных, если она не существует."""
        try:
            logger.info("Подключение к MySQL для создания базы данных")
            conn = await wait_for(
                aiomysql.connect(
                    host=host_db,
                    port=port_db,
                    user=user_db,
                    password=user_db_password,
                    charset="utf8mb4",
                    autocommit=True,
                ),
                timeout=1.0,
            )
            async with conn.cursor() as cursor:
                await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                logger.info(f"База данных '{
                            db_name}' создана или уже существует")
            conn.close()
            await conn.ensure_closed()
        except TimeoutError:
            logger.error("Таймаут при подключении к базе данных")
        except Exception as e:
            logger.error(f"Ошибка при создании базы данных: {e}")

    async def create_pool(self):
        """Создание пула соединений с базой данных."""
        try:
            self.pool = await aiomysql.create_pool(
                host=host_db,
                port=port_db,
                user=user_db,
                password=user_db_password,
                db=db_name,
                cursorclass=aiomysql.DictCursor,  # Используем DictCursor по умолчанию
                autocommit=True,
            )
            logger.info("Пул соединений успешно создан.")
        except Exception as e:
            logger.error(f"Ошибка при создании пула соединений: {e}")

    async def close_pool(self):
        """Закрытие пула соединений."""
        if self.pool:
            self.pool.close()
            await asyncio.wait_for(self.pool.wait_closed(), timeout=1.0)
            logger.info("Пул соединений закрыт")
    """Инициализация базы данных и создание необходимых таблиц."""

    async def init_db(self):
        """Инициализация базы данных и создание необходимых таблиц."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return

        logger.info("Инициализация базы данных")
        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS calls_zubr (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            call_recording VARCHAR(255),
                            company VARCHAR(255),
                            source VARCHAR(255),
                            keyword VARCHAR(255),
                            advertisement VARCHAR(255),
                            call_duration VARCHAR(255),
                            call_date DATETIME,
                            employee VARCHAR(255),
                            employee_ext_number VARCHAR(255),
                            caller_number VARCHAR(255),
                            unique_call VARCHAR(255),
                            unique_target_call VARCHAR(255),
                            number_pool_name VARCHAR(255),
                            channel VARCHAR(255),
                            substitution_type VARCHAR(255),
                            call_id VARCHAR(255)
                        )
                        """
                    )
                    logger.info("Таблицы созданы или уже существуют")
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")

    async def insert_call_data_zubr(self, call_data):
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False
        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO calls_zubr (
                            call_recording,
                            company,
                            source,
                            keyword,
                            advertisement,
                            call_duration,
                            call_date,
                            employee,
                            employee_ext_number,
                            caller_number,
                            unique_call,
                            unique_target_call,
                            number_pool_name,
                            channel,
                            substitution_type,
                            call_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            call_data["call_recording"],
                            call_data["company"],
                            call_data["source"],
                            call_data["keyword"],
                            call_data["advertisement"],
                            call_data["call_duration"],
                            call_data["call_date"],
                            call_data["employee"],
                            call_data["employee_ext_number"],
                            call_data["caller_number"],
                            call_data["unique_call"],
                            call_data["unique_target_call"],
                            call_data["number_pool_name"],
                            call_data["channel"],
                            call_data["substitution_type"],
                            call_data["call_id"]
                        ),
                    )
                    await connection.commit()
                    logger.info(
                        f"Данные успешно добавлены в таблицу calls_zubr: {call_data}")
            return True
        except Exception as e:
            logger.error(
                f"Ошибка при добавлении данных в таблицу calls_zubr: {e}")
            return False


# Для тестирования модуля отдельно (можно удалить, если не нужно)
if __name__ == "__main__":

    async def main():
        db_initializer = DatabaseInitializer()
        await db_initializer.create_database()  # Создаем базу данных
        await db_initializer.create_pool()  # Создаем пул соединений
        await db_initializer.init_db()  # Инициализируем базу данных (создаем таблицы)
        await db_initializer.close_pool()  # Закрываем пул

    asyncio.run(main())
