import aiomysql
import asyncio
from dotenv import load_dotenv
from configuration.logger_setup import logger
import os
from typing import Optional, Dict, Any
from asyncio import TimeoutError, wait_for


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

    """Инициализация базы данных и создание необходимых таблиц."""

    async def init_db(self):
        """Инициализация базы данных и создание необходимых таблиц."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return

        logger.info("Инициализация базы данных")

        try:
            # Сначала ждем выполнения корутины, затем используем результат в блоке with
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor() as cursor:
                    try:
                        # Создание таблицы Контактов
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS contacts (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            name VARCHAR(255),               # Имя
                            surname VARCHAR(255),            # Фамилия
                            formal_title VARCHAR(255)        # Обращение
                        )"""
                        )

                        # Создание таблицы Телефонных Номеров
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS contacts_phone_numbers (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            contact_id INT,
                            phone_number VARCHAR(255),       # Телефонный номер
                            FOREIGN KEY (contact_id) REFERENCES contacts(id)
                        )"""
                        )

                        # Создание таблицы Email
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS contacts_emails (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            contact_id INT,
                            email VARCHAR(255),              # Электронный адрес
                            FOREIGN KEY (contact_id) REFERENCES contacts(id)
                        )"""
                        )

                        # Создание таблицы Банковских Счетов
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS contacts_bank_accounts (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            contact_id INT,
                            bank_name VARCHAR(255),          # Название банка
                            account_number VARCHAR(255),     # Номер счета
                            currency VARCHAR(50),            # Валюта
                            FOREIGN KEY (contact_id) REFERENCES contacts(id)
                        )"""
                        )

                        # Создание таблицы Менеджеров
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS contact_managers (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            contact_id INT,
                            manager_contact_id INT,          # ID контакта-менеджера
                            FOREIGN KEY (contact_id) REFERENCES contacts(id),
                            FOREIGN KEY (manager_contact_id) REFERENCES contacts(id)
                        )"""
                        )

                        # Создание таблицы Статусов Контакта
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS contact_status (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            contact_id INT,
                            status_description VARCHAR(255), # Описание статуса
                            FOREIGN KEY (contact_id) REFERENCES contacts(id)
                        )"""
                        )

                        # Создание таблицы Истории Взаимодействий
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS contacts_interaction_history (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            contact_id INT,
                            interaction_type VARCHAR(255),   # Тип взаимодействия
                            interaction_date DATETIME,       # Дата взаимодействия
                            commentary VARCHAR(1024),        # Комментарии
                            FOREIGN KEY (contact_id) REFERENCES contacts(id)
                        )"""
                        )

                        # Создание таблицы Адресов
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS contacts_addresses (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            contact_id INT,
                            address_line1 VARCHAR(255),      # Адресная строка 1
                            address_line2 VARCHAR(255),      # Адресная строка 2
                            city VARCHAR(255),               # Город
                            state VARCHAR(255),              # Область/штат
                            zip_code VARCHAR(50),            # Почтовый индекс
                            country VARCHAR(50),             # Страна
                            FOREIGN KEY (contact_id) REFERENCES contacts(id)
                        )"""
                        )

                        # Создание таблицы Вызовов
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS calls (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            id_call INT,
                            date_and_time DATETIME,
                            client_id INT,
                            phone_number VARCHAR(255),
                            company_number VARCHAR(255),
                            call_type VARCHAR(255),
                            client_status VARCHAR(255),
                            interaction_status VARCHAR(255),
                            employee VARCHAR(255),
                            commentary VARCHAR(255),
                            action VARCHAR(255),
                            FOREIGN KEY (client_id) REFERENCES contacts(id)
                        )
                        """
                        )

                        logger.info("Таблицы созданы или уже существуют")
                    except Exception as e:
                        logger.error(f"Ошибка при инициализации базы данных: {e}")
        except asyncio.TimeoutError:
            logger.error("Таймаут при попытке получить соединение из пула")

    async def close_pool(self):
        """Закрытие пула соединений."""
        if self.pool:
            self.pool.close()
            await asyncio.wait_for(self.pool.wait_closed(), timeout=1.0)
            logger.info("Пул соединений закрыт")

    """Получение всех данных о контактах с возможностью фильтрации."""

    async def get_all_contact_data(self, filters: Optional[Dict[str, Any]] = None):
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    try:
                        # Получаем список всех таблиц, начинающихся с 'contacts_'
                        await cursor.execute("SHOW TABLES LIKE 'contacts_%'")
                        tables = await cursor.fetchall()
                        contact_tables = [list(row.values())[0] for row in tables]

                        # Формируем базовый SQL-запрос
                        base_query = """
                            SELECT c.id AS contact_id, c.name, c.surname, c.formal_title
                            FROM contacts c
                        """
                        join_queries = (
                            []
                        )  # Для хранения SQL-запросов для объединения таблиц
                        select_fields = []  # Для хранения полей, которые нужно выбрать
                        where_clauses = []  # Для условий фильтрации
                        parameters = []  # Для значений параметров фильтрации

                        alias_counter = 1  # Счетчик для создания уникальных алиасов
                        for table in contact_tables:
                            table_suffix = table.split("_", 1)[
                                1
                            ]  # Получаем суффикс после "contacts_"
                            table_alias = f"{table_suffix[:2]}{alias_counter}"  # Создаем уникальный алиас
                            join_field = f"{table_alias}.contact_id"
                            join_queries.append(
                                f"LEFT JOIN {table} {table_alias} ON c.id = {join_field}"
                            )

                            await cursor.execute(f"SHOW COLUMNS FROM {table}")
                            columns = await cursor.fetchall()
                            for column in columns:
                                column_name = column["Field"]
                                if column_name != "contact_id":
                                    select_fields.append(f"{table_alias}.{column_name}")
                                    # Если в фильтрах есть значение для этой колонки, добавляем его в WHERE
                                    if filters and column_name in filters:
                                        where_clauses.append(
                                            f"{table_alias}.{column_name} = %s"
                                        )
                                        parameters.append(filters[column_name])

                            alias_counter += 1

                        full_query = f"SELECT c.id AS contact_id, c.name, c.surname, c.formal_title, {', '.join(select_fields)} FROM contacts c {' '.join(join_queries)}"

                        # Добавляем динамические условия фильтрации
                        if filters:
                            base_filters = ["name", "surname", "formal_title"]
                            for key, value in filters.items():
                                if key in base_filters:
                                    where_clauses.append(f"c.{key} = %s")
                                    parameters.append(value)

                            if where_clauses:
                                full_query += " WHERE " + " AND ".join(where_clauses)

                        logger.info(f"Выполнение SQL-запроса: {full_query}")
                        await cursor.execute(full_query, tuple(parameters))
                        result = await cursor.fetchall()

                        return result
                    except Exception as e:
                        logger.error(
                            f"Ошибка при получении данных из всех таблиц contacts_: {e}"
                        )
                        return []
        except asyncio.TimeoutError:
            logger.error("Таймаут при попытке получить соединение из пула")
            return []

    async def insert_call_data(self, call_data):
        """Добавление данных о вызове в таблицу calls."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO calls (id_call, date_and_time, client_id, phone_number, company_number, call_type, client_status, interaction_status, employee, commentary, action)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                        (
                            call_data["id_call"],
                            call_data["date_and_time"],
                            call_data["client_id"],
                            call_data["phone_number"],
                            call_data["company_number"],
                            call_data["call_type"],
                            call_data["client_status"],
                            call_data["interaction_status"],
                            call_data["employee"],
                            call_data["commentary"],
                            call_data.get("action", None),
                        ),
                    )
                    await connection.commit()
                    logger.info(
                        f"Данные успешно добавлены в таблицу calls: {call_data}"
                    )
            return True
        except asyncio.TimeoutError:
            logger.error("Таймаут при попытке получить соединение из пула")
            return False
        except Exception as e:
            logger.error(f"Ошибка при добавлении данных в таблицу calls: {e}")
            return False

    async def insert_contact(self, contact_data):
        """Добавление данных о контакте в таблицу contacts."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO contacts (name, surname, formal_title)
                        VALUES (%s, %s, %s)
                    """,
                        (
                            contact_data["name"],
                            contact_data["surname"],
                            contact_data["formal_title"],
                        ),
                    )
                    await connection.commit()
                    logger.info(
                        f"Данные успешно добавлены в таблицу contacts: {contact_data}"
                    )
            return True
        except asyncio.TimeoutError:
            logger.error("Таймаут при попытке получить соединение из пула")
            return False
        except Exception as e:
            logger.error(f"Ошибка при добавлении данных в таблицу contacts: {e}")
            return False

    async def insert_contact_phone_number(self, phone_data):
        """Добавление данных о телефонном номере в таблицу contacts_phone_numbers."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False
        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO contacts_phone_numbers (contact_id, phone_number)
                        VALUES (%s, %s)
                    """,
                        (
                            phone_data["contact_id"],
                            phone_data["phone_number"],
                        ),
                    )
                    await connection.commit()
                    logger.info(
                        f"Данные успешно добавлены в таблицу contacts_phone_numbers: {phone_data}"
                    )
            return True
        except Exception as e:
            logger.error(
                f"Ошибка при добавлении данных в таблицу contacts_phone_numbers: {e}"
            )
            return False

    async def insert_contact_email(self, email_data):
        """Добавление данных о электронном адресе в таблицу contacts_emails."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False
        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO contacts_emails (contact_id, email)
                        VALUES (%s, %s)
                    """,
                        (
                            email_data["contact_id"],
                            email_data["email"],
                        ),
                    )
                    await connection.commit()
                    logger.info(
                        f"Данные успешно добавлены в таблицу contacts_emails: {email_data}"
                    )
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении данных в таблицу contacts_emails: {e}")
            return False

    async def insert_contact_bank_account(self, bank_account_data):
        """Добавление данных о банковском счете в таблицу contacts_bank_accounts."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False
        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO contacts_bank_accounts (contact_id, bank_name, account_number, currency)
                        VALUES (%s, %s, %s, %s)
                    """,
                        (
                            bank_account_data["contact_id"],
                            bank_account_data["bank_name"],
                            bank_account_data["account_number"],
                            bank_account_data["currency"],
                        ),
                    )
                    await connection.commit()
                    logger.info(
                        f"Данные успешно добавлены в таблицу contacts_bank_accounts: {bank_account_data}"
                    )
            return True
        except Exception as e:
            logger.error(
                f"Ошибка при добавлении данных в таблицу contacts_bank_accounts: {e}"
            )
            return False

    async def insert_contact_manager(self, manager_data):
        """Добавление данных о менеджере контакта в таблицу contact_managers."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False
        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO contact_managers (contact_id, manager_contact_id)
                        VALUES (%s, %s)
                    """,
                        (
                            manager_data["contact_id"],
                            manager_data["manager_contact_id"],
                        ),
                    )
                    await connection.commit()
                    logger.info(
                        f"Данные успешно добавлены в таблицу contact_managers: {manager_data}"
                    )
            return True
        except Exception as e:
            logger.error(
                f"Ошибка при добавлении данных в таблицу contact_managers: {e}"
            )
            return False

    async def insert_contact_status(self, status_data):
        """Добавление данных о статусе контакта в таблицу contact_status."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False
        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO contact_status (contact_id, status_description)
                        VALUES (%s, %s)
                    """,
                        (
                            status_data["contact_id"],
                            status_data["status_description"],
                        ),
                    )
                    await connection.commit()
                    logger.info(
                        f"Данные успешно добавлены в таблицу contact_status: {status_data}"
                    )
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении данных в таблицу contact_status: {e}")
            return False

    async def insert_contact_interaction_history(self, interaction_data):
        """Добавление данных о взаимодействии контакта в таблицу contacts_interaction_history."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False
        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO contacts_interaction_history (contact_id, interaction_type, interaction_date, commentary)
                        VALUES (%s, %s, %s, %s)
                    """,
                        (
                            interaction_data["contact_id"],
                            interaction_data["interaction_type"],
                            interaction_data["interaction_date"],
                            interaction_data["commentary"],
                        ),
                    )
                    await connection.commit()
                    logger.info(
                        f"Данные успешно добавлены в таблицу contacts_interaction_history: {interaction_data}"
                    )
            return True
        except Exception as e:
            logger.error(
                f"Ошибка при добавлении данных в таблицу contacts_interaction_history: {e}"
            )
            return False

    async def insert_contact_address(self, address_data):
        """Добавление данных об адресе в таблицу contacts_addresses."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False
        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO contacts_addresses (contact_id, address_line1, address_line2, city, state, zip_code, country)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                        (
                            address_data["contact_id"],
                            address_data["address_line1"],
                            address_data["address_line2"],
                            address_data["city"],
                            address_data["state"],
                            address_data["zip_code"],
                            address_data["country"],
                        ),
                    )
                    await connection.commit()
                    logger.info(
                        f"Данные успешно добавлены в таблицу contacts_addresses: {address_data}"
                    )
            return True
        except Exception as e:
            logger.error(
                f"Ошибка при добавлении данных в таблицу contacts_addresses: {e}"
            )
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
