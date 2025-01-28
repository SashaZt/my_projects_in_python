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
user_db = os.getenv("MYSQL_USER")
user_db_password = os.getenv("MYSQL_PASSWORD")
host_db = os.getenv("HOST_DB")
port_db = int(os.getenv("PORT_DB", 3306))
db_name = os.getenv("MYSQL_DATABASE")
logger.info(f"Host: {host_db}, Port: {port_db}, User: {user_db}, DB: {db_name}")



async def wait_for_db():
    """Ожидание доступности базы данных."""
    logger.info("Проверяем доступность базы данных...")
    for _ in range(10):  # Попытки подключения (10 раз)
        try:
            conn = await aiomysql.connect(
                host=host_db,
                port=port_db,
                user=user_db,
                password=user_db_password,
                db=db_name,
                autocommit=True,
            )
            conn.close()
            logger.info("База данных доступна!")
            return True
        except Exception as e:
            logger.warning(f"База данных недоступна, повтор через 5 секунды: {e}")
            await asyncio.sleep(5)
    logger.error("Не удалось подключиться к базе данных после 10 попыток.")
    raise TimeoutError("База данных не доступна")


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
                logger.info(f"База данных '{db_name}' создана или уже существует")
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
                            utm_campaign VARCHAR(255),
                            utm_source VARCHAR(255),
                            utm_term VARCHAR(255),
                            utm_content VARCHAR(255),
							utm_medium VARCHAR(255),
                            call_duration VARCHAR(255),
                            call_date DATETIME,
                            employee VARCHAR(255),
                            employee_ext_number VARCHAR(255),
                            caller_number VARCHAR(255),
                            unique_call VARCHAR(255),
                            unique_target_call VARCHAR(255),
                            number_pool_name VARCHAR(255),
                            substitution_type VARCHAR(255),
                            call_id VARCHAR(255),
                            talk_time VARCHAR(255)
                        )
                        """
                    )
                    await cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS calls_data (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            date DATETIME,
                            phone VARCHAR(20),
                            line VARCHAR(255),
                            manager_name VARCHAR(255),
                            call_text_ukr TEXT,
                            overview TEXT,
                            notes TEXT,
                            mp3_link VARCHAR(255),
                            file_name VARCHAR(255),
                            transcript_id VARCHAR(255)
                        )
                        """
                    )
                    logger.info("Таблицы созданы или уже существуют")
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")

    # Добавляем новый метод для проверки существования transcript_id
    async def check_transcript_exists(self, transcript_id: str) -> bool:
        """Проверяет существование записи с указанным transcript_id."""
        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    query = """
                    SELECT COUNT(*) 
                    FROM calls_data 
                    WHERE transcript_id = %s
                    """
                    await cursor.execute(query, (transcript_id,))
                    result = await cursor.fetchone()
                    exists = result is not None and result[0] > 0
                    logger.debug(f"Проверка transcript_id={transcript_id}: result={result}, exists={exists}")
                    return exists
        except Exception as e:
            logger.error(f"Ошибка при проверке transcript_id в БД: {e}")
            return False
            
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
                            utm_campaign,
                            utm_source,
                            utm_term,
                            utm_content,
                            call_duration,
                            call_date,
                            employee,
                            employee_ext_number,
                            caller_number,
                            unique_call,
                            unique_target_call,
                            number_pool_name,
                            utm_medium,
                            substitution_type,
                            call_id,
                            talk_time
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            call_data["call_recording"],
                            call_data["utm_campaign"],
                            call_data["utm_source"],
                            call_data["utm_term"],
                            call_data["utm_content"],
                            call_data["call_duration"],
                            call_data["call_date"],
                            call_data["employee"],
                            call_data["employee_ext_number"],
                            call_data["caller_number"],
                            call_data["unique_call"],
                            call_data["unique_target_call"],
                            call_data["number_pool_name"],
                            call_data["utm_medium"],
                            call_data["substitution_type"],
                            call_data["call_id"],
                            call_data["talk_time"],
                        ),
                    )
                    await connection.commit()
                    logger.info(
                        f"Данные успешно добавлены в таблицу calls_zubr: {call_data}"
                    )
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении данных в таблицу calls_zubr: {e}")
            return False
    

    async def insert_call_data(self, data: dict) -> bool:
        """Вставляет данные в таблицу calls_data."""
        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    # Преобразуем формат даты
                    date_str = data["date"].replace('_', ' ')
                    
                    query = """
                    INSERT INTO calls_data (
                        date, phone, line, manager_name, call_text_ukr,
                        overview, notes, mp3_link, file_name, transcript_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    await cursor.execute(query, (
                        date_str,
                        data["phone"],
                        data["line"],
                        data["manager_name"],
                        data["call_text_ukr"],
                        data["overview"],
                        data["notes"],
                        data["mp3_link"],
                        data["file_name"],
                        data["transcript_id"]
                    ))
                    await connection.commit()
                    return True
        except Exception as e:
            logger.error(f"Ошибка при вставке данных в БД: {e}")
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
