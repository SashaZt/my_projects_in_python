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
                        await cursor.execute("""
                            -- Создание таблицы для хранения информации о контактах
                            CREATE TABLE IF NOT EXISTS contacts (
                                id INT AUTO_INCREMENT PRIMARY KEY,  -- Уникальный идентификатор контакта, автоинкремент
                                username VARCHAR(255) NOT NULL,  -- Имя пользователя
                                contact_type VARCHAR(255) NOT NULL,  -- Тип контакта (например, физическое лицо, компания и т.д.)
                                contact_status VARCHAR(255) NOT NULL,  -- Статус контакта (например, первый контакт, в работе и т.д.)
                                manager VARCHAR(255),  -- Имя менеджера, ответственного за контакт
                                userphone VARCHAR(20),  -- Телефонный номер контакта
                                useremail VARCHAR(255),  -- Электронная почта контакта
                                usersite VARCHAR(255),  -- Веб-сайт контакта
                                comment TEXT  -- Комментарии к контакту
                            );
                        """)
                                        
                        await cursor.execute("""
                            -- Создание таблицы для хранения информации о дополнительных контактах, связанных с основным контактом
                            CREATE TABLE IF NOT EXISTS additional_contacts (
                                id INT AUTO_INCREMENT PRIMARY KEY,  -- Уникальный идентификатор записи, автоинкремент
                                contact_id INT,  -- Идентификатор основного контакта, внешний ключ
                                name VARCHAR(255),  -- Имя дополнительного контакта
                                position VARCHAR(255),  -- Должность дополнительного контакта
                                phone VARCHAR(20),  -- Телефонный номер дополнительного контакта
                                email VARCHAR(255),  -- Электронная почта дополнительного контакта
                                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE  -- Внешний ключ, ссылающийся на таблицу contacts, при удалении основного контакта все связанные записи удаляются
                            );
                        """)
                                        
                        await cursor.execute("""
                            -- Создание таблицы для хранения информации о мессенджерах, связанных с контактом
                            CREATE TABLE IF NOT EXISTS messengers_data (
                                id INT AUTO_INCREMENT PRIMARY KEY,  -- Уникальный идентификатор записи, автоинкремент
                                contact_id INT,  -- Идентификатор основного контакта, внешний ключ
                                messenger VARCHAR(255),  -- Название мессенджера (например, Telegram, WhatsApp)
                                link VARCHAR(255),  -- Ссылка на мессенджер
                                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE  -- Внешний ключ, ссылающийся на таблицу contacts, при удалении основного контакта все связанные записи удаляются
                            );
                        """)
                                        
                        await cursor.execute("""
                            -- Создание таблицы для хранения платежных реквизитов, связанных с контактом
                            CREATE TABLE IF NOT EXISTS payment_details (
                                id INT AUTO_INCREMENT PRIMARY KEY,  -- Уникальный идентификатор записи, автоинкремент
                                contact_id INT,  -- Идентификатор основного контакта, внешний ключ
                                IBAN VARCHAR(255),  -- Номер банковского счета в формате IBAN
                                bank_name VARCHAR(255),  -- Название банка
                                SWIFT VARCHAR(255),  -- SWIFT-код банка
                                account_type VARCHAR(255),  -- Тип счета (например, расчетный, сберегательный)
                                currency VARCHAR(50),  -- Валюта счета
                                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE  -- Внешний ключ, ссылающийся на таблицу contacts, при удалении основного контакта все связанные записи удаляются
                            );
                        """)
                                        
                        await cursor.execute("""
                            -- Создание таблицы для хранения комментариев, связанных с контактом
                            CREATE TABLE IF NOT EXISTS comments (
                                id INT AUTO_INCREMENT PRIMARY KEY,  -- Уникальный идентификатор записи, автоинкремент
                                contact_id INT,  -- Идентификатор основного контакта, внешний ключ
                                date DATE,  -- Дата комментария
                                manager VARCHAR(255),  -- Имя менеджера, оставившего комментарий
                                comment TEXT,  -- Текст комментария
                                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE  -- Внешний ключ, ссылающийся на таблицу contacts, при удалении основного контакта все связанные записи удаляются
                            );
                        """)

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

    async def get_comments(self, contact_id):
        """Получить комментарии для данного контакта."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT date, manager, comment FROM comments WHERE contact_id = %s",
                        (contact_id,)
                    )
                    comments = await cursor.fetchall()
                    return comments
        except Exception as e:
            logger.error(f"Ошибка при получении комментариев: {e}")
            return []

    async def get_payment_details(self, contact_id):
        """Получить платежные реквизиты для данного контакта."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT IBAN, bank_name, SWIFT, account_type, currency FROM payment_details WHERE contact_id = %s",
                        (contact_id,)
                    )
                    payment_details = await cursor.fetchall()
                    return payment_details
        except Exception as e:
            logger.error(f"Ошибка при получении платежных данных: {e}")
            return []

    async def get_additional_contacts(self, contact_id):
        """Получить дополнительные контакты для данного контакта."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT name, position, phone, email FROM additional_contacts WHERE contact_id = %s",
                        (contact_id,)
                    )
                    additional_contacts = await cursor.fetchall()
                    return additional_contacts
        except Exception as e:
            logger.error(f"Ошибка при получении дополнительных контактов: {e}")
            return []

    async def get_messengers_data(self, contact_id):
        """Получить данные мессенджеров для данного контакта."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT messenger, link FROM messengers_data WHERE contact_id = %s",
                        (contact_id,)
                    )
                    messengers_data = await cursor.fetchall()
                    return messengers_data
        except Exception as e:
            logger.error(f"Ошибка при получении данных мессенджеров: {e}")
            return []

    async def get_contact_by_id(self, contact_id):
        """Получить данные контакта по ID."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return None

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT * FROM contacts WHERE id = %s", (contact_id,))
                    contact = await cursor.fetchone()
                    return contact
        except Exception as e:
            logger.error(f"Ошибка при получении данных контакта: {e}")
            return None

    # Реализация методов для извлечения дополнительных данных аналогична.
    # Например, метод get_additional_contacts:
    async def get_additional_contacts(self, contact_id):
        """Получить дополнительные контакты для данного контакта."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT name, position, phone, email FROM additional_contacts WHERE contact_id = %s", (contact_id,))
                    additional_contacts = await cursor.fetchall()
                    return additional_contacts
        except Exception as e:
            logger.error(f"Ошибка при получении дополнительных контактов: {e}")
            return []

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
                        INSERT INTO contacts (username, contact_type, contact_status, manager, userphone, useremail, usersite, comment)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            contact_data["username"],  # Используем правильное название столбца: username
                            contact_data["contact_type"],
                            contact_data["contact_status"],
                            contact_data["manager"],
                            contact_data["userphone"],
                            contact_data["useremail"],
                            contact_data["usersite"],
                            contact_data["comment"],
                        ),
                    )
                    await connection.commit()
                    contact_id = cursor.lastrowid  # Получаем ID вставленного контакта
                    logger.info(f"Данные успешно добавлены в таблицу contacts: {contact_data}")
                    return contact_id
        except Exception as e:
            logger.error(f"Ошибка при добавлении данных в таблицу contacts: {e}")
            return False
    async def insert_or_update_payment_details(self, payment_data):
        """Вставка или обновление платежных данных."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO payment_details (contact_id, IBAN, bank_name, SWIFT, account_type, currency)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            payment_data["contact_id"],
                            payment_data["IBAN"],
                            payment_data["BankName"],
                            payment_data["SWIFT"],
                            payment_data["AccountType"],
                            payment_data["Currency"],
                        ),
                    )
                    await connection.commit()
                    logger.info(f"Платежные данные успешно добавлены: {payment_data}")
                    return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении платежных данных: {e}")
            return False

    async def insert_or_update_messenger_data(self, messenger_data):
        """Вставка или обновление данных мессенджера."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO messengers_data (contact_id, messenger, link)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            messenger_data["contact_id"],
                            messenger_data["messenger"],
                            messenger_data["link"],
                        ),
                    )
                    await connection.commit()
                    logger.info(f"Данные мессенджера успешно добавлены: {messenger_data}")
                    return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении данных мессенджера: {e}")
            return False

    async def insert_or_update_additional_contact(self, additional_contact_data):
        """Вставка или обновление дополнительного контакта."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor() as cursor:
                    # Предположим, что здесь у нас нет уникального идентификатора для обновления
                    await cursor.execute(
                        """
                        INSERT INTO additional_contacts (contact_id, name, position, phone, email)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            additional_contact_data["contact_id"],
                            additional_contact_data["name"],
                            additional_contact_data["position"],
                            additional_contact_data["phone"],
                            additional_contact_data["email"],
                        ),
                    )
                    await connection.commit()
                    logger.info(f"Дополнительный контакт успешно добавлен: {additional_contact_data}")
                    return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении дополнительного контакта: {e}")
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
