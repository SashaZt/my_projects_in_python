import asyncio
import os
from asyncio import TimeoutError, wait_for
from typing import Any, Dict, List, Optional
from datetime import datetime

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
                        # Таблица метаданных
                        """Эта таблица будет использоваться для хранения информации о динамически добавляемых столбцах. Это позволяет вашему приложению отслеживать, какие дополнительные столбцы были добавлены в каждую таблицу, и каков их тип данных."""
                        await cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS table_metadata (
                                id INT AUTO_INCREMENT PRIMARY KEY,  # Уникальный идентификатор для каждой записи. AUTO_INCREMENT автоматически увеличивает значение с каждой новой записью.
                                table_name VARCHAR(255) NOT NULL,   # Название таблицы, к которой относится данная запись (например, 'contacts'). Используем тип VARCHAR(255), так как название таблицы - это строка.
                                column_name VARCHAR(255) NOT NULL,  # Название столбца, который добавляется динамически. Также используем тип VARCHAR(255), так как это строка.
                                data_type VARCHAR(50) NOT NULL      # Тип данных для данного столбца (например, 'VARCHAR(255)', 'INT', 'DATETIME'). Мы используем тип VARCHAR(50), так как тип данных - это тоже строка, и обычно его длина не превышает 50 символов.
                            );
                        """
                        )

                        await cursor.execute(
                            """
                            -- Создание таблицы для хранения информации о контактах
                            CREATE TABLE IF NOT EXISTS contacts (
                                id INT AUTO_INCREMENT PRIMARY KEY,  -- Уникальный идентификатор контакта, автоинкремент
                                username VARCHAR(255) NOT NULL,  -- Организация
                                contact_type VARCHAR(255) NOT NULL,  -- Тип контакта (например, физическое лицо, компания и т.д.)
                                contact_status VARCHAR(255) NOT NULL,  -- Статус контакта (например, первый контакт, в работе и т.д.)
                                manager VARCHAR(255),  -- Имя менеджера, ответственного за контакт
                                userphone VARCHAR(20),  -- Телефонный номер контакта
                                useremail VARCHAR(255),  -- Электронная почта контакта
                                usersite VARCHAR(255),  -- Веб-сайт контакта
                                comment TEXT,  -- Комментарии к контакту
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- Дата и время создания контакта
                                

                            );
                        """
                        )

                        await cursor.execute(
                            """
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
                        """
                        )

                        await cursor.execute(
                            """
                            -- Создание таблицы для хранения информации о мессенджерах, связанных с контактом
                            CREATE TABLE IF NOT EXISTS messengers_data (
                                id INT AUTO_INCREMENT PRIMARY KEY,  -- Уникальный идентификатор записи, автоинкремент
                                contact_id INT,  -- Идентификатор основного контакта, внешний ключ
                                messenger VARCHAR(255),  -- Название мессенджера (например, Telegram, WhatsApp)
                                link VARCHAR(255),  -- Ссылка на мессенджер
                                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE  -- Внешний ключ, ссылающийся на таблицу contacts, при удалении основного контакта все связанные записи удаляются
                            );
                        """
                        )

                        await cursor.execute(
                            """
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
                        """
                        )

                        await cursor.execute(
                            """
                            -- Создание таблицы для хранения комментариев, связанных с контактом
                            CREATE TABLE IF NOT EXISTS comments (
                                id INT AUTO_INCREMENT PRIMARY KEY,  -- Уникальный идентификатор записи, автоинкремент
                                contact_id INT,  -- Идентификатор основного контакта, внешний ключ
                                date DATE,  -- Дата комментария
                                manager VARCHAR(255),  -- Имя менеджера, оставившего комментарий
                                comment TEXT,  -- Текст комментария
                                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE  -- Внешний ключ, ссылающийся на таблицу contacts, при удалении основного контакта все связанные записи удаляются
                            );
                        """
                        )
                        await cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS tasks (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            title VARCHAR(255),
                            status VARCHAR(50),
                            note TEXT,
                            initiator VARCHAR(255),  -- Может быть ID или email
                            performers TEXT,  -- Массив исполнителей в виде строки, например "performer1,performer2"
                            reviewers TEXT,   -- Массив проверяющих в виде строки
                            start_time DATETIME,
                            end_time DATETIME,
                            control_time DATETIME
                        );"""
                        )
                        await cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS task_contacts (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            task_id INT,
                            contact_id INT,
                            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                            FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
                        );"""
                        )
                        await cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS task_documents (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            task_id INT,
                            file_name VARCHAR(255),
                            file_path TEXT,
                            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                        );"""
                        )

                        # Сначала создаем таблицу statements
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS statements (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            statement_text TEXT  -- Пример поля для заявок
                            );
                        """
                        )

                        await cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS task_statements (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            task_id INT,
                            statement_id INT,
                            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                            FOREIGN KEY (statement_id) REFERENCES statements(id) ON DELETE CASCADE
                        );"""
                        )

                        # # Создание таблицы Вызовов
                        # await cursor.execute(
                        #     """
                        # CREATE TABLE IF NOT EXISTS calls (
                        #     id INT AUTO_INCREMENT PRIMARY KEY,
                        #     id_call INT,
                        #     date_and_time DATETIME,
                        #     client_id INT,
                        #     phone_number VARCHAR(255),
                        #     company_number VARCHAR(255),
                        #     call_type VARCHAR(255),
                        #     client_status VARCHAR(255),
                        #     interaction_status VARCHAR(255),
                        #     employee VARCHAR(255),
                        #     commentary VARCHAR(255),
                        #     action VARCHAR(255),
                        #     FOREIGN KEY (client_id) REFERENCES contacts(id)
                        # )
                        # """
                        # )
                        # Создание таблицы Вызовов
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS calls (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            caller_id VARCHAR(255),  -- Уникальный идентификатор звонка
                            call_type VARCHAR(255),  -- Тип вызова
                            call_date DATETIME,  -- Дата и время вызова
                            who_is_connected VARCHAR(255),  -- С кем соеденили
                            call_status VARCHAR(255),  -- Статус вызова
                            you_call VARCHAR(255),  -- Куда звонили
                            employee_extension_number VARCHAR(255),  -- Внутренний номер сотрудника
                            callers_number VARCHAR(255),  -- Номер звонившего
                            link_record VARCHAR(255),  -- Ссылка на запись звонка
                            duration_of_conversation VARCHAR(50),  -- Длительность разговора
                            call_duration VARCHAR(50),  -- Общая длительность вызова
                            waiting_time VARCHAR(50),  -- Время ожидания
                            client_id INT,  -- Идентификатор клиента
                            FOREIGN KEY (client_id) REFERENCES contacts(id)
                        )
                        """
                        )

                        # Создаем таблицу config, если она еще не существует
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS config (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            config_key VARCHAR(255) NOT NULL,
                            config_value TEXT NOT NULL
                        );
                        """
                        )
                        await cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS modules (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                module_name VARCHAR(255) NOT NULL,
                                module_id VARCHAR(255) NOT NULL
                            );
                            """
                        )

                        await cursor.execute(
                            """
                            -- Создание пустой таблицы modules
                            CREATE TABLE IF NOT EXISTS modules (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                module_name VARCHAR(255) NOT NULL,
                                module_id VARCHAR(255) NOT NULL UNIQUE
                            );
                            """
                        )

                        await cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS permissions (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                access_rights VARCHAR(10) NOT NULL,
                                explanation TEXT NOT NULL
                            );
                            """
                        )

                        await cursor.execute(
                            """
                            INSERT INTO permissions (id, access_rights, explanation) VALUES
                            (1, '100', 'Читает свои'),
                            (2, '101', 'Читает и просматривает свои (входит в Заявку/Звонок…)'),
                            (3, '110', 'Читает и пишет свои (без входа)'),
                            (4, '111', 'Читает, пишет и просматривает (входит) свои'),
                            (5, '1000', 'Читает записи всех'),
                            (6, '1101', 'Читает и просматривает всех'),
                            (7, '1110', 'Читает и редактирует всех'),
                            (8, '1111', 'Читает и редактирует всех'),
                            (9, '11111', 'Читает, редактирует и просматривает всех (все права, админ)')
                            ON DUPLICATE KEY UPDATE access_rights=VALUES(access_rights);
                            """
                        )

                        await cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS module_permissions (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                module_id INT,
                                permission_id INT,
                                FOREIGN KEY (module_id) REFERENCES modules(id),
                                FOREIGN KEY (permission_id) REFERENCES permissions(id)
                            );
                            """
                        )

                        await cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS roles (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                role_name VARCHAR(255) NOT NULL,
                                description TEXT
                            );
                            """
                        )

                        await cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS role_permissions (
                                role_id INT,
                                module_id INT,
                                access_rights VARCHAR(10),
                                FOREIGN KEY (role_id) REFERENCES roles(id),
                                FOREIGN KEY (module_id) REFERENCES modules(id)
                            );
                            """
                        )
                        await cursor.execute(
                            """
                        CREATE TABLE IF NOT EXISTS tasks_extended (
                            id INT AUTO_INCREMENT PRIMARY KEY,  # Уникальный идентификатор записи, автоинкремент
                            name VARCHAR(255) NOT NULL,  # Название задачи, обязательно для заполнения
                            prior INT,  # Приоритет задачи, числовое значение
                            note TEXT,  # Заметки к задаче, текстовое поле
                            initiator VARCHAR(255),  # Инициатор задачи, строковое значение (например, имя или email)
                            performers TEXT,  # Исполнители задачи, хранится как строка (например, "исполнитель1, исполнитель2")
                            reviewer VARCHAR(255),  # Проверяющий задачу, строковое значение
                            startTime DATETIME,  # Время начала выполнения задачи
                            endTime DATETIME,  # Время окончания выполнения задачи
                            controlTime DATETIME,  # Время контроля выполнения задачи
                            contacts TEXT,  # Контактные данные, связанные с задачей, текстовое поле
                            applications TEXT,  # Заявки, связанные с задачей, текстовое поле
                            documents TEXT,  # Документы, связанные с задачей, текстовое поле
                            status VARCHAR(50),  # Статус задачи, строковое значение (например, "в процессе", "завершено")
                            comments TEXT  # Комментарии к задаче, текстовое поле
                        );
                        """
                        )
                        # Создаем таблицу
                        await cursor.execute(
                            """
                            CREATE TABLE IF NOT EXISTS telegram_messages (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            sender_name VARCHAR(255),         -- Имя отправителя
                            sender_username VARCHAR(255),     -- Username отправителя
                            sender_id BIGINT,                 -- Telegram ID отправителя
                            sender_phone VARCHAR(20),         -- Телефон отправителя
                            sender_type VARCHAR(50),          -- Тип отправителя (Пользователь, Бот, Канал, Группа)
                            recipient_name VARCHAR(255),      -- Имя получателя
                            recipient_username VARCHAR(255),  -- Username получателя
                            recipient_id BIGINT,              -- Telegram ID получателя
                            recipient_phone VARCHAR(20),      -- Телефон получателя
                            message TEXT,                     -- Текст сообщения
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP -- Время создания записи
                        );
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

    """Добавление данных о вызове в таблицу calls."""

    # async def insert_call_data(self, call_data):

    #     if self.pool is None:
    #         logger.error("Пул соединений не инициализирован.")
    #         return False

    #     try:
    #         connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
    #         async with connection:
    #             async with connection.cursor() as cursor:
    #                 await cursor.execute(
    #                     """
    #                     INSERT INTO calls (id_call, date_and_time, client_id, phone_number, company_number, call_type, client_status, interaction_status, employee, commentary, action)
    #                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    #                 """,
    #                     (
    #                         call_data["id_call"],
    #                         call_data["date_and_time"],
    #                         call_data["client_id"],
    #                         call_data["phone_number"],
    #                         call_data["company_number"],
    #                         call_data["call_type"],
    #                         call_data["client_status"],
    #                         call_data["interaction_status"],
    #                         call_data["employee"],
    #                         call_data["commentary"],
    #                         call_data.get("action", None),
    #                     ),
    #                 )
    #                 await connection.commit()
    #                 logger.info(
    #                     f"Данные успешно добавлены в таблицу calls: {call_data}"
    #                 )
    #         return True
    #     except asyncio.TimeoutError:
    #         logger.error("Таймаут при попытке получить соединение из пула")
    #         return False
    #     except Exception as e:
    #         logger.error(f"Ошибка при добавлении данных в таблицу calls: {e}")
    #         return False
    async def insert_call_data(self, call_data):
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO calls (
                            caller_id, call_type, call_date, who_is_connected, call_status,
                            you_call, employee_extension_number, callers_number,
                            link_record, duration_of_conversation, call_duration,
                            waiting_time, client_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            call_data["caller_id"],
                            call_data["call_type"],
                            call_data["call_date"],
                            call_data["who_is_connected"],
                            call_data["call_status"],
                            call_data["you_call"],
                            call_data["employee_extension_number"],
                            call_data["callers_number"],
                            call_data["link_record"],
                            call_data["duration_of_conversation"],
                            call_data["call_duration"],
                            call_data["waiting_time"],
                            call_data["client_id"],
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

    """Получить комментарии для данного контакта. по ТЗ"""

    async def get_comments(self, contact_id):

        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT date, manager, comment FROM comments WHERE contact_id = %s",
                        (contact_id,),
                    )
                    comments = await cursor.fetchall()
                    return comments
        except Exception as e:
            logger.error(f"Ошибка при получении комментариев: {e}")
            return []

    """Получить платежные реквизиты для данного контакта. по ТЗ"""

    async def get_payment_details(self, contact_id):

        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT IBAN, bank_name, SWIFT, account_type, currency FROM payment_details WHERE contact_id = %s",
                        (contact_id,),
                    )
                    payment_details = await cursor.fetchall()
                    return payment_details
        except Exception as e:
            logger.error(f"Ошибка при получении платежных данных: {e}")
            return []

    """Получить дополнительные контакты для данного контакта. по ТЗ"""

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
                        (contact_id,),
                    )
                    additional_contacts = await cursor.fetchall()
                    return additional_contacts
        except Exception as e:
            logger.error(f"Ошибка при получении дополнительных контактов: {e}")
            return []

    """Получить данные мессенджеров для данного контакта. по ТЗ"""

    async def get_messengers_data(self, contact_id):

        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT messenger, link FROM messengers_data WHERE contact_id = %s",
                        (contact_id,),
                    )
                    messengers_data = await cursor.fetchall()
                    return messengers_data
        except Exception as e:
            logger.error(f"Ошибка при получении данных мессенджеров: {e}")
            return []

    """Получить данные контакта по ID. по ТЗ"""

    async def get_contact_by_id(self, contact_id):

        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return None

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT * FROM contacts WHERE id = %s", (contact_id,)
                    )
                    contact = await cursor.fetchone()
                    return contact
        except Exception as e:
            logger.error(f"Ошибка при получении данных контакта: {e}")
            return None

    """Получить дополнительные контакты для данного контакта. по ТЗ"""

    async def get_additional_contacts(self, contact_id):

        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT name, position, phone, email FROM additional_contacts WHERE contact_id = %s",
                        (contact_id,),
                    )
                    additional_contacts = await cursor.fetchall()
                    return additional_contacts
        except Exception as e:
            logger.error(f"Ошибка при получении дополнительных контактов: {e}")
            return []

    """Добавление данных о контакте в таблицу contacts. по ТЗ"""

    async def insert_contact(self, contact_data):

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
                            contact_data[
                                "username"
                            ],  # Используем правильное название столбца: username
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
                    logger.info(
                        f"Данные успешно добавлены в таблицу contacts: {contact_data}"
                    )
                    return contact_id
        except Exception as e:
            logger.error(f"Ошибка при добавлении данных в таблицу contacts: {e}")
            return False

    async def save_statements(self, task_id: int, statements: List[int]):
        """Сохранение заявок, связанных с задачей"""
        if self.pool is None:
            raise Exception("Пул соединений не инициализирован.")

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    # Удаляем существующие заявки для данной задачи
                    await cursor.execute(
                        "DELETE FROM task_statements WHERE task_id = %s", (task_id,)
                    )

                    # Добавляем новые заявки
                    for statement_id in statements:
                        await cursor.execute(
                            """
                            INSERT INTO task_statements (task_id, statement_id)
                            VALUES (%s, %s)
                        """,
                            (task_id, statement_id),
                        )

                await connection.commit()
        except Exception as e:
            raise Exception(f"Ошибка при сохранении заявок для задачи: {e}")

    async def create_contact(
        self,
        contact_id: int,
        username: str = "Новый контакт",
        contact_type: str = "Тип",
        contact_status: str = "Новый",
    ):
        """Создаем новый контакт в таблице contacts"""
        if self.pool is None:
            raise Exception("Пул соединений не инициализирован.")

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    # Создаем новый контакт
                    await cursor.execute(
                        """
                        INSERT INTO contacts (id, username, contact_type, contact_status, manager, userphone, useremail, usersite, comment)
                        VALUES (%s, %s, %s, %s, 'Менеджер', '0000000000', 'email@example.com', 'website.com', 'Автоматически создан контакт')
                    """,
                        (contact_id, username, contact_type, contact_status),
                    )
                    await connection.commit()
        except Exception as e:
            raise Exception(f"Ошибка при создании контакта: {e}")

    async def save_contacts(self, task_id: int, contacts: List[int]):
        """Сохранение контактов, связанных с задачей"""
        if self.pool is None:
            raise Exception("Пул соединений не инициализирован.")

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    # Удаляем существующие контакты для данной задачи (если нужно обновить контакты)
                    await cursor.execute(
                        "DELETE FROM task_contacts WHERE task_id = %s", (task_id,)
                    )

                    # Добавляем новые контакты
                    for contact_id in contacts:
                        await cursor.execute(
                            """
                            INSERT INTO task_contacts (task_id, contact_id)
                            VALUES (%s, %s)
                        """,
                            (task_id, contact_id),
                        )

                await connection.commit()
        except Exception as e:
            raise Exception(f"Ошибка при сохранении контактов для задачи: {e}")

    """Вставка или обновление платежных данных. по ТЗ"""

    async def insert_or_update_payment_details(self, payment_data):

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

    """Вставка или обновление данных мессенджера. по ТЗ"""

    async def insert_or_update_messenger_data(self, messenger_data):

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
                    logger.info(
                        f"Данные мессенджера успешно добавлены: {messenger_data}"
                    )
                    return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении данных мессенджера: {e}")
            return False

    """Вставка или обновление дополнительного контакта. по ТЗ"""

    async def insert_or_update_additional_contact(self, additional_contact_data):

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
                    logger.info(
                        f"Дополнительный контакт успешно добавлен: {additional_contact_data}"
                    )
                    return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении дополнительного контакта: {e}")
            return False

    async def get_dynamic_columns(self, table_name: str):
        """Получает список всех столбцов в таблице, включая динамически добавленные."""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                    columns = await cursor.fetchall()
                    column_names = [column["Field"] for column in columns]
                    return column_names
        except Exception as e:
            logger.error(f"Ошибка при получении столбцов таблицы {table_name}: {e}")
            return []

    async def get_documents_by_task_id(self, task_id: int) -> List[dict]:
        """Получение документов, связанных с задачей по её ID"""
        if self.pool is None:
            raise Exception("Пул соединений не инициализирован.")

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    # Получаем документы, связанные с задачей
                    await cursor.execute(
                        """
                        SELECT file_name, file_path 
                        FROM task_documents 
                        WHERE task_id = %s
                    """,
                        (task_id,),
                    )
                    documents = await cursor.fetchall()

                    return [
                        {"file_name": doc["file_name"], "file_path": doc["file_path"]}
                        for doc in documents
                    ]
        except Exception as e:
            raise Exception(f"Ошибка при получении документов для задачи: {e}")

    async def get_task_by_id(self, task_id: int) -> Optional[dict]:
        """Получение задания по его ID"""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return None

        try:
            connection = await asyncio.wait_for(self.pool.acquire(), timeout=1.0)
            async with connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    # Запрос к базе данных для получения задания по ID
                    await cursor.execute(
                        "SELECT * FROM tasks WHERE id = %s", (task_id,)
                    )
                    task = await cursor.fetchone()

                    if task is None:
                        return None

                    # Получение связанных данных (контакты, заявки, документы)
                    await cursor.execute(
                        "SELECT contact_id FROM task_contacts WHERE task_id = %s",
                        (task_id,),
                    )
                    contacts = await cursor.fetchall()

                    await cursor.execute(
                        "SELECT statement_id FROM task_statements WHERE task_id = %s",
                        (task_id,),
                    )
                    statements = await cursor.fetchall()

                    await cursor.execute(
                        "SELECT file_name, file_path FROM task_documents WHERE task_id = %s",
                        (task_id,),
                    )
                    documents = await cursor.fetchall()

                    # Возвращаем структуру данных задачи
                    task_data = {
                        "id": task["id"],
                        "title": task["title"],
                        "status": task["status"],
                        "note": task["note"],
                        "initiator": task["initiator"],
                        "performers": task["performers"].split(
                            ","
                        ),  # Преобразуем строку в список
                        "reviewers": task["reviewers"].split(
                            ","
                        ),  # Преобразуем строку в список
                        "startTime": task["start_time"].strftime("%Y-%m-%dT%H:%M:%S"),
                        "endTime": task["end_time"].strftime("%Y-%m-%dT%H:%M:%S"),
                        "controlTime": task["control_time"].strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        ),
                        "contacts": [contact["contact_id"] for contact in contacts],
                        "statements": [
                            statement["statement_id"] for statement in statements
                        ],
                        "documents": [
                            {
                                "file_name": doc["file_name"],
                                "file_path": doc["file_path"],
                            }
                            for doc in documents
                        ],
                    }

                    return task_data
        except Exception as e:
            logger.error(f"Ошибка при получении задания: {e}")
            return None

    async def save_task_data(self, task_data: dict) -> int:
        """Сохранение данных задачи в базу данных"""
        if self.pool is None:
            raise Exception("Пул соединений не инициализирован.")

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    # SQL-запрос для вставки данных задачи
                    await cursor.execute(
                        """
                        INSERT INTO tasks (title, status, note, initiator, performers, reviewers, start_time, end_time, control_time)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                        (
                            task_data["title"],
                            task_data["status"],
                            task_data["note"],
                            task_data["initiator"],
                            ",".join(
                                task_data["performers"]
                            ),  # Преобразуем список в строку
                            ",".join(
                                task_data["reviewers"]
                            ),  # Преобразуем список в строку
                            task_data["startTime"],
                            task_data["endTime"],
                            task_data["controlTime"],
                        ),
                    )
                    # Получаем ID вставленной записи
                    await connection.commit()
                    task_id = cursor.lastrowid
                    return task_id
        except Exception as e:
            raise Exception(f"Ошибка при сохранении данных задачи: {e}")

    async def statement_exists(self, statement_id: int) -> bool:
        """Проверяем, существует ли заявка с данным ID"""
        if self.pool is None:
            raise Exception("Пул соединений не инициализирован.")

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        "SELECT id FROM statements WHERE id = %s", (statement_id,)
                    )
                    result = await cursor.fetchone()
                    return result is not None
        except Exception as e:
            raise Exception(f"Ошибка при проверке заявки: {e}")

    async def create_statement(self, statement_id: int, statement_text: str):
        """Создаем новую заявку в таблице statements"""
        if self.pool is None:
            raise Exception("Пул соединений не инициализирован.")

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    # Создаем новую заявку
                    await cursor.execute(
                        """
                        INSERT INTO statements (id, statement_text) VALUES (%s, %s)
                    """,
                        (statement_id, statement_text),
                    )
                    await connection.commit()
        except Exception as e:
            raise Exception(f"Ошибка при создании заявки: {e}")

    async def contact_exists(self, contact_id: int) -> bool:
        """Проверяем, существует ли контакт с данным ID"""
        if self.pool is None:
            raise Exception("Пул соединений не инициализирован.")

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    # Выполняем запрос для проверки существования контакта
                    await cursor.execute(
                        "SELECT id FROM contacts WHERE id = %s", (contact_id,)
                    )
                    result = await cursor.fetchone()
                    return result is not None
        except Exception as e:
            raise Exception(f"Ошибка при проверке контакта: {e}")

    async def save_config_to_db(self, config_data: Dict[str, str]):
        """Сохраняет конфигурационные данные в таблицу config в формате ключ-значение"""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return False

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    # Очищаем существующие конфигурационные данные
                    await cursor.execute("TRUNCATE TABLE config")

                    # Сохраняем новые конфигурационные данные
                    for key, value in config_data.items():
                        await cursor.execute(
                            """
                            INSERT INTO config (config_key, config_value)
                            VALUES (%s, %s)
                        """,
                            (key, value),
                        )

                await connection.commit()
                logger.info("Конфигурационные данные успешно сохранены")
                return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении конфигурационных данных: {e}")
            return False

    async def get_config(self) -> Dict[str, str]:
        """Получает конфигурационные данные из таблицы config"""
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return {}

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT config_key, config_value FROM config")
                    result = await cursor.fetchall()

                    # Преобразуем результат в словарь
                    config_data = {
                        row["config_key"]: row["config_value"] for row in result
                    }
                    return config_data
        except Exception as e:
            logger.error(f"Ошибка при получении конфигурационных данных: {e}")
            return {}

    async def insert_telegram_message_to_db(self, message_data: dict):
        """
        Сохраняет сообщение Telegram в базу данных.

        :param message_data: Словарь с данными сообщения.
        :return: None
        """
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return

        sql = """
            INSERT INTO telegram_messages (
                sender_name, sender_username, sender_id, sender_phone, sender_type,
                recipient_name, recipient_username, recipient_id, recipient_phone, message, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        values = (
            message_data["sender_name"],
            message_data["sender_username"],
            message_data["sender_id"],
            message_data["sender_phone"],
            message_data["sender_type"],
            message_data["recipient_name"],
            message_data["recipient_username"],
            message_data["recipient_id"],
            message_data["recipient_phone"],
            message_data["message"],
        )

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(sql, values)
                    await connection.commit()
                    logger.info("Сообщение успешно сохранено в базу данных.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении сообщения в базу данных: {e}")

    async def get_all_telegram_messages(self) -> List[dict]:
        """
        Получает все сообщения из таблицы telegram_messages.

        :return: Список словарей с данными сообщений.
        """
        if self.pool is None:
            logger.error("Пул соединений не инициализирован.")
            return []

        sql = """
            SELECT sender_name, sender_username, sender_id, sender_phone, sender_type,
                recipient_name, recipient_username, recipient_id, recipient_phone, message, created_at
            FROM telegram_messages
        """

        try:
            async with self.pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql)
                    messages = await cursor.fetchall()

                    # Преобразуем created_at из datetime в строку
                    for message in messages:
                        if isinstance(message["created_at"], datetime):
                            message["created_at"] = message["created_at"].isoformat()

                    return messages
        except Exception as e:
            logger.error(f"Ошибка при получении сообщений из базы данных: {e}")
            return []


# Для тестирования модуля отдельно (можно удалить, если не нужно)
if __name__ == "__main__":

    async def main():
        db_initializer = DatabaseInitializer()
        await db_initializer.create_database()  # Создаем базу данных
        await db_initializer.create_pool()  # Создаем пул соединений
        await db_initializer.init_db()  # Инициализируем базу данных (создаем таблицы)
        await db_initializer.close_pool()  # Закрываем пул

    asyncio.run(main())
