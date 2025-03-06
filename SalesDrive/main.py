import asyncio
import json
import os.path
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import aiosqlite
import gspread
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from gspread.utils import rowcol_to_a1
from loguru import logger
from oauth2client.service_account import ServiceAccountCredentials

# Глобальные переменные
metadata = None
config = None

# Путь к папкам и файлу для данных
current_directory = Path.cwd()
data_directory = current_directory / "data"
log_directory = current_directory / "log"
config_directory = current_directory / "config"
db_directory = current_directory / "db"
CONFIG_PATH = config_directory / "config.json"
XML_PATH = current_directory / "export.xml"


def load_config():
    """Загрузка конфигурации из JSON-файла"""
    global config

    try:
        # Проверяем, существует ли файл конфигурации
        if not os.path.exists(CONFIG_PATH):
            logger.error(f"Ошибка: файл конфигурации не найден: {CONFIG_PATH}")
            logger.error("Создайте файл конфигурации на основе примера.")
            sys.exit(1)

        # Загружаем конфигурацию
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Проверяем наличие необходимых разделов
        required_sections = ["database", "google_sheets"]
        for section in required_sections:
            if section not in config:
                logger.error(
                    f"Ошибка: в файле конфигурации отсутствует раздел '{section}'"
                )
                sys.exit(1)

        # Проверяем наличие необходимых параметров
        if "path" not in config["database"]:
            logger.error("Ошибка: не указан путь к базе данных (database.path)")
            sys.exit(1)

        if "credentials_path" not in config["google_sheets"]:
            logger.error(
                "Ошибка: не указан путь к учетным данным Google (google_sheets.credentials_path)"
            )
            sys.exit(1)

        if "spreadsheet_id" not in config["google_sheets"]:
            logger.error(
                "Ошибка: не указан ID таблицы Google Sheets (google_sheets.spreadsheet_id)"
            )
            sys.exit(1)

        return config

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при чтении файла конфигурации: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при загрузке конфигурации: {e}")
        sys.exit(1)


# Инициализация директорий
db_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)

# Настройка логирования
logger.remove()
logger.add(
    log_directory / "log_message.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)

# Загружаем конфигурацию после настройки логирования
config = load_config()


# Определяем пути и параметры на основе конфигурации
SALESDRIVE_API = config["salesdrive"]["api"]
DB_PATH = config["database"]["path"]
GOOGLE_CREDENTIALS_PATH = config["google_sheets"]["credentials_path"]
SPREADSHEET_ID = config["google_sheets"]["spreadsheet_id"]
SHEET_NAME = config["google_sheets"]["sheet_name"]

recordings_output_file = data_directory / "recording.json"
service_account_file = config_directory / "service_account.json"
log_file_path = log_directory / "log_message.log"


def load_metadata_from_json(json_data):
    """
    Загружает метаданные из JSON-данных, полученных от SalesDrive

    Args:
        json_data: Словарь с данными из SalesDrive, содержащий ключи 'data' и 'meta'

    Returns:
        Словарь с обработанными метаданными
    """
    global metadata

    # Если метаданные уже загружены, вернем их
    if metadata is not None:
        return metadata

    try:
        # Проверяем наличие метаданных в JSON
        if "meta" not in json_data:
            logger.error("В JSON-данных отсутствует секция 'meta'")
            return {}

        meta_section = json_data["meta"]

        # Проверяем наличие полей в метаданных
        if "fields" not in meta_section:
            logger.error("В метаданных отсутствует секция 'fields'")
            return {}

        fields = meta_section["fields"]

        # Создаем словарь для хранения обработанных метаданных
        processed_metadata = {}

        # Обрабатываем tipProdazu1
        if "tipProdazu1" in fields:
            tip_field = fields["tipProdazu1"]
            options = tip_field.get("options", [])

            # Создаем соответствие ID -> текст
            tip_mapping = {}
            for option in options:
                value = option.get("value")
                text = option.get("text")
                if value is not None and text:
                    tip_mapping[value] = text

            processed_metadata["tipProdazu1"] = tip_mapping
            logger.info(f"Загружено {len(tip_mapping)} вариантов tipProdazu1")

        # Обрабатываем typeId
        if "typeId" in fields:
            type_field = fields["typeId"]
            options = type_field.get("options", [])

            # Создаем соответствие ID -> текст
            type_mapping = {}
            for option in options:
                value = option.get("value")
                text = option.get("text")
                if value is not None and text:
                    type_mapping[value] = text

            processed_metadata["typeId"] = type_mapping
            logger.info(f"Загружено {len(type_mapping)} вариантов typeId")

        # Обрабатываем statusId
        if "statusId" in fields:
            type_field = fields["statusId"]
            options = type_field.get("options", [])

            # Создаем соответствие ID -> текст
            type_mapping = {}
            for option in options:
                value = option.get("value")
                text = option.get("text")
                if value is not None and text:
                    type_mapping[value] = text

            processed_metadata["statusId"] = type_mapping
            logger.info(f"Загружено {len(type_mapping)} вариантов statusId")

        # Обрабатываем shipping_method
        if "shipping_method" in fields:
            type_field = fields["shipping_method"]
            options = type_field.get("options", [])

            # Создаем соответствие ID -> текст
            type_mapping = {}
            for option in options:
                value = option.get("value")
                text = option.get("text")
                if value is not None and text:
                    type_mapping[value] = text

            processed_metadata["shipping_method"] = type_mapping
            logger.info(f"Загружено {len(type_mapping)} вариантов shipping_method")

        # Обрабатываем payment_method
        if "payment_method" in fields:
            type_field = fields["payment_method"]
            options = type_field.get("options", [])

            # Создаем соответствие ID -> текст
            type_mapping = {}
            for option in options:
                value = option.get("value")
                text = option.get("text")
                if value is not None and text:
                    type_mapping[value] = text

            processed_metadata["payment_method"] = type_mapping
            logger.info(f"Загружено {len(type_mapping)} вариантов payment_method")

        # Здесь можно добавить обработку других полей по мере необходимости

        # Сохраняем обработанные метаданные в глобальную переменную
        metadata = processed_metadata

        return processed_metadata

    except Exception as e:
        logger.error(f"Ошибка при обработке метаданных: {e}")
        return {}


def get_salesdrive_orders():
    try:
        # Получаем текущий год и предыдущий год
        current_date = datetime.now()
        current_year = current_date.year
        previous_year = current_year - 1

        # Создаем даты: с начала предыдущего года до конца текущего
        date_from = datetime(previous_year, 1, 1, 0, 0, 0)
        date_to = datetime(current_year, 12, 31, 23, 59, 59)

        # Форматируем даты
        date_from_str = date_from.strftime("%Y-%m-%d %H:%M:%S")
        date_to_str = date_to.strftime("%Y-%m-%d %H:%M:%S")

        # Базовый URL
        base_url = "https://leia.salesdrive.me/api/order/list/"

        # Формируем строку запроса вручную
        status_params = "&".join(
            [f"filter[statusId][]={status}" for status in [1, 2, 3, 4]]
        )
        query_string = f"filter[orderTime][from]={requests.utils.quote(date_from_str)}&filter[orderTime][to]={requests.utils.quote(date_to_str)}&{status_params}&page=1&limit=100"
        full_url = f"{base_url}?{query_string}"

        logger.info(f"Запрашиваем заказы с {date_from_str} по {date_to_str}")
        logger.info(f"URL запроса: {full_url}")

        headers = {"Form-Api-Key": SALESDRIVE_API}

        response = requests.get(
            full_url,
            headers=headers,
            timeout=(10, 30),  # (connect timeout, read timeout)
        )

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Получено заказов: {len(data.get('data', []))}")
            write_recordings_to_json(recordings_output_file, data)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_order(recordings_output_file))
            loop.close()
        else:
            logger.error(f"Ошибка API: {response.status_code}, Текст: {response.text}")
            raise Exception(
                f"API request failed with status code: {response.status_code}"
            )

    except requests.exceptions.Timeout:
        logger.error("Timeout при запросе к API")
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        raise


# Получить старые данные
def get_salesdrive_orders_old_data():
    try:
        # Получаем текущий год и предыдущий год
        current_date = datetime.now()
        current_year = current_date.year
        previous_year = current_year - 1

        # Создаем даты: с начала предыдущего года до конца текущего
        date_from = datetime(previous_year, 1, 1, 0, 0, 0)
        date_to = datetime(current_year, 12, 31, 23, 59, 59)

        # Форматируем даты
        date_from_str = date_from.strftime("%Y-%m-%d %H:%M:%S")
        date_to_str = date_to.strftime("%Y-%m-%d %H:%M:%S")

        # Базовый URL
        base_url = "https://leia.salesdrive.me/api/order/list/"

        # Формируем строку запроса вручную
        status_params = "&".join(
            [f"filter[statusId][]={status}" for status in [1, 2, 3, 4]]
        )

        page = 14
        query_string = f"filter[orderTime][from]={requests.utils.quote(date_from_str)}&filter[orderTime][to]={requests.utils.quote(date_to_str)}&page={page}&limit=100"
        full_url = f"{base_url}?{query_string}"

        logger.info(f"Запрашиваем заказы с {date_from_str} по {date_to_str}")
        logger.info(f"URL запроса: {full_url}")

        headers = {"Form-Api-Key": SALESDRIVE_API}

        response = requests.get(
            full_url,
            headers=headers,
            timeout=(10, 30),  # (connect timeout, read timeout)
        )
        output_file = data_directory / f"recording_0{page}.json"
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Получено заказов: {len(data.get('data', []))}")
            write_recordings_to_json(output_file, data)
        else:
            logger.error(f"Ошибка API: {response.status_code}, Текст: {response.text}")
            raise Exception(
                f"API request failed with status code: {response.status_code}"
            )

    except requests.exceptions.Timeout:
        logger.error("Timeout при запросе к API")
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        raise


def write_recordings_to_json(data_output_file, data):
    # Сохраняем данные в файл result.json
    with open(data_output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def create_database():
    """Создание базы данных и таблиц со всеми полями из JSON"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Основная таблица заказов
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            formId INTEGER,
            version INTEGER,
            organizationId INTEGER,
            shipping_method TEXT,
            payment_method TEXT,
            shipping_address TEXT,
            comment TEXT,
            timeEntryOrder TEXT,
            holderTime TEXT,
            document_ord_check TEXT,
            discountAmount REAL,
            orderTime TEXT,
            updateAt TEXT,
            statusId TEXT,
            paymentDate TEXT,
            rejectionReason TEXT,
            userId INTEGER,
            paymentAmount REAL,
            commissionAmount REAL,
            costPriceAmount REAL,
            shipping_costs REAL,
            expensesAmount REAL,
            profitAmount REAL,
            typeId TEXT,
            payedAmount REAL,
            restPay REAL,
            call TEXT,
            sajt INTEGER,
            externalId TEXT,
            utmPage TEXT,
            utmMedium TEXT,
            campaignId INTEGER,
            utmSourceFull TEXT,
            utmSource TEXT,
            utmCampaign TEXT,
            utmContent TEXT,
            utmTerm TEXT,
            uploaded_to_sheets BOOLEAN DEFAULT FALSE,
            last_update_exported TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            orderTimeLook TEXT  -- Добавлена новая колонка
        )
        """
        )

        # Таблица для данных о доставке
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS delivery_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            senderId INTEGER,
            backDelivery INTEGER,
            cityName TEXT,
            provider TEXT,
            payForDelivery TEXT,
            type TEXT,
            trackingNumber TEXT,
            statusCode INTEGER,
            deliveryDateAndTime TEXT,
            idEntity INTEGER,
            branchNumber INTEGER,
            address TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
        """
        )

        # Таблица для первичного контакта
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS primary_contacts (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            formId INTEGER,
            version INTEGER,
            active INTEGER,
            con_uGC TEXT,
            con_bloger TEXT,
            lName TEXT,
            fName TEXT,
            mName TEXT,
            telegram TEXT,
            instagramNick TEXT,
            counterpartyId INTEGER,
            comment TEXT,
            userId INTEGER,
            createTime TEXT,
            leadsCount INTEGER,
            leadsSalesCount INTEGER,
            leadsSalesAmount REAL,
            company TEXT,
            con_povnaOplata TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
        """
        )

        # Таблица для телефонов контакта
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS contact_phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            phone TEXT,
            FOREIGN KEY (contact_id) REFERENCES primary_contacts (id)
        )
        """
        )

        # Таблица для email контакта
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS contact_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            email TEXT,
            FOREIGN KEY (contact_id) REFERENCES primary_contacts (id)
        )
        """
        )

        # Таблица для контактов (аналогично primary_contacts)
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            formId INTEGER,
            version INTEGER,
            active INTEGER,
            con_uGC TEXT,
            con_bloger TEXT,
            lName TEXT,
            fName TEXT,
            mName TEXT,
            telegram TEXT,
            instagramNick TEXT,
            counterpartyId INTEGER,
            comment TEXT,
            userId INTEGER,
            createTime TEXT,
            leadsCount INTEGER,
            leadsSalesCount INTEGER,
            leadsSalesAmount REAL,
            company TEXT,
            con_povnaOplata TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
        """
        )

        # Таблица для телефонов других контактов
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS other_contact_phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            phone TEXT,
            FOREIGN KEY (contact_id) REFERENCES contacts (id)
        )
        """
        )

        # Таблица для email других контактов
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS other_contact_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            email TEXT,
            FOREIGN KEY (contact_id) REFERENCES contacts (id)
        )
        """
        )

        # Таблица для продуктов
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            amount INTEGER,
            percentCommission REAL,
            preSale INTEGER,
            productId INTEGER,
            price REAL,
            stockId INTEGER,
            costPrice REAL,
            discount REAL,
            description TEXT,
            commission REAL,
            percentDiscount REAL,
            parameter TEXT,
            text TEXT,
            barcode TEXT,
            documentName TEXT,
            manufacturer TEXT,
            sku TEXT,
            uktzed TEXT,
            included_in_set BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (order_id) REFERENCES orders (id)
            
        )
        """
        )

        # Таблица для tipProdazu1 (массив)
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS tip_prodazu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            value TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
        """
        )

        # Таблица для dzereloKomentarVidKlienta (массив)
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS dzerelo_komentar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            value TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
        """
        )
        # Создаем таблицу категорий
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS product_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            category_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # Создаем таблицу связей товаров с категориями
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS product_category_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (productId),
            FOREIGN KEY (category_id) REFERENCES product_categories (category_id),
            UNIQUE(product_id, category_id)
        )
        """
        )
        await db.commit()
        logger.info("База данных создана успешно")


async def insert_order_data(
    db,
    order_id,
    order_data,
    typeId_text,
    statusId_text,
    payment_method_text,
    shipping_method_text,
):
    """Вставка нового заказа в БД"""
    try:
        if not order_id:
            logger.info("Ошибка: отсутствует ID заказа в данных")
            return False
        order_time = order_data.get("orderTime")
        order_time_look = ""
        if order_time:
            try:
                # Парсим дату из строки формата "2024-08-03 09:22:04"
                dt = datetime.strptime(order_time, "%Y-%m-%d %H:%M:%S")
                # Форматируем в нужный формат "08.2024"
                order_time_look = dt.strftime("%m.%Y")
            except:
                # В случае ошибки оставляем пустую строку
                order_time_look = ""

        # Вставляем основные данные заказа
        await db.execute(
            """
            INSERT INTO orders (
                id, formId, version, organizationId, shipping_method, payment_method,
                shipping_address, comment, timeEntryOrder, holderTime, document_ord_check,
                discountAmount, orderTime, updateAt, statusId, paymentDate, rejectionReason,
                userId, paymentAmount, commissionAmount, costPriceAmount, shipping_costs,
                expensesAmount, profitAmount, typeId, payedAmount, restPay, call, sajt,
                externalId, utmPage, utmMedium, campaignId, utmSourceFull, utmSource,
                utmCampaign, utmContent, utmTerm, uploaded_to_sheets,orderTimeLook
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, FALSE,?
            )
            """,
            (
                order_data.get("id"),
                order_data.get("formId"),
                order_data.get("version"),
                order_data.get("organizationId"),
                shipping_method_text,
                payment_method_text,
                order_data.get("shipping_address"),
                order_data.get("comment"),
                order_data.get("timeEntryOrder"),
                order_data.get("holderTime"),
                order_data.get("document_ord_check"),
                order_data.get("discountAmount"),
                order_data.get("orderTime"),
                order_data.get("updateAt"),
                statusId_text,
                order_data.get("paymentDate"),
                order_data.get("rejectionReason"),
                order_data.get("userId"),
                order_data.get("paymentAmount"),
                order_data.get("commissionAmount"),
                order_data.get("costPriceAmount"),
                order_data.get("shipping_costs"),
                order_data.get("expensesAmount"),
                order_data.get("profitAmount"),
                typeId_text,
                order_data.get("payedAmount"),
                order_data.get("restPay"),
                order_data.get("call"),
                order_data.get("sajt"),
                order_data.get("externalId"),
                order_data.get("utmPage"),
                order_data.get("utmMedium"),
                order_data.get("campaignId"),
                order_data.get("utmSourceFull"),
                order_data.get("utmSource"),
                order_data.get("utmCampaign"),
                order_data.get("utmContent"),
                order_data.get("utmTerm"),
                order_time_look,
            ),
        )

        # Вставляем данные о доставке
        ord_delivery_data = order_data.get("ord_delivery_data", [])
        if ord_delivery_data is not None:  # Проверка на None
            for delivery in ord_delivery_data:
                await db.execute(
                    """
                INSERT INTO delivery_data (
                    order_id, senderId, backDelivery, cityName, provider, payForDelivery,
                    type, trackingNumber, statusCode, deliveryDateAndTime, idEntity,
                    branchNumber, address
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        order_id,
                        delivery.get("senderId"),
                        delivery.get("backDelivery"),
                        delivery.get("cityName"),
                        delivery.get("provider"),
                        delivery.get("payForDelivery"),
                        delivery.get("type"),
                        delivery.get("trackingNumber"),
                        delivery.get("statusCode"),
                        delivery.get("deliveryDateAndTime"),
                        delivery.get("idEntity"),
                        delivery.get("branchNumber"),
                        delivery.get("address"),
                    ),
                )

            # Вставляем данные первичного контакта
            primary_contact = order_data.get("primaryContact")
            if primary_contact:
                contact_id = primary_contact.get("id")

                # Проверяем, существует ли контакт с таким ID
                cursor = await db.execute(
                    "SELECT id FROM primary_contacts WHERE id = ?", (contact_id,)
                )
                existing_contact = await cursor.fetchone()

                if not existing_contact:
                    # Вставляем только если контакта еще нет
                    await db.execute(
                        """
                    INSERT INTO primary_contacts (
                        id, order_id, formId, version, active, con_uGC, con_bloger,
                        lName, fName, mName, telegram, instagramNick, counterpartyId,
                        comment, userId, createTime, leadsCount, leadsSalesCount,
                        leadsSalesAmount, company, con_povnaOplata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            contact_id,
                            order_id,
                            primary_contact.get("formId"),
                            primary_contact.get("version"),
                            primary_contact.get("active"),
                            primary_contact.get("con_uGC"),
                            primary_contact.get("con_bloger"),
                            primary_contact.get("lName"),
                            primary_contact.get("fName"),
                            primary_contact.get("mName"),
                            primary_contact.get("telegram"),
                            primary_contact.get("instagramNick"),
                            primary_contact.get("counterpartyId"),
                            primary_contact.get("comment"),
                            primary_contact.get("userId"),
                            primary_contact.get("createTime"),
                            primary_contact.get("leadsCount"),
                            primary_contact.get("leadsSalesCount"),
                            primary_contact.get("leadsSalesAmount"),
                            primary_contact.get("company"),
                            primary_contact.get("con_povnaOplata"),
                        ),
                    )
                else:
                    logger.info(
                        f"Контакт с ID {contact_id} уже существует в базе данных"
                    )

                # Вставляем телефоны и email первичного контакта
                phone_list = primary_contact.get("phone", [])
                if phone_list is not None:  # Проверка на None
                    for phone in phone_list:
                        await db.execute(
                            "INSERT INTO contact_phones (contact_id, phone) VALUES (?, ?)",
                            (contact_id, phone),
                        )

                email_list = primary_contact.get("email", [])
                if email_list is not None:  # Проверка на None
                    for email in email_list:
                        await db.execute(
                            "INSERT INTO contact_emails (contact_id, email) VALUES (?, ?)",
                            (contact_id, email),
                        )

            # Вставляем данные других контактов
            contacts_list = order_data.get("contacts", [])
            if contacts_list is not None:  # Проверка на None
                for contact in contacts_list:
                    contact_id = contact.get("id")

                    # Проверяем, существует ли контакт с таким ID
                    cursor = await db.execute(
                        "SELECT id FROM contacts WHERE id = ?", (contact_id,)
                    )
                    existing_contact = await cursor.fetchone()

                    if not existing_contact:
                        # Вставляем только если контакта еще нет
                        await db.execute(
                            """
                        INSERT INTO contacts (
                            id, order_id, formId, version, active, con_uGC, con_bloger,
                            lName, fName, mName, telegram, instagramNick, counterpartyId,
                            comment, userId, createTime, leadsCount, leadsSalesCount,
                            leadsSalesAmount, company, con_povnaOplata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                contact_id,
                                order_id,
                                contact.get("formId"),
                                contact.get("version"),
                                contact.get("active"),
                                contact.get("con_uGC"),
                                contact.get("con_bloger"),
                                contact.get("lName"),
                                contact.get("fName"),
                                contact.get("mName"),
                                contact.get("telegram"),
                                contact.get("instagramNick"),
                                contact.get("counterpartyId"),
                                contact.get("comment"),
                                contact.get("userId"),
                                contact.get("createTime"),
                                contact.get("leadsCount"),
                                contact.get("leadsSalesCount"),
                                contact.get("leadsSalesAmount"),
                                contact.get("company"),
                                contact.get("con_povnaOplata"),
                            ),
                        )
                    else:
                        logger.info(
                            f"Контакт с ID {contact_id} уже существует в таблице contacts"
                        )

                    # Вставляем телефоны и email других контактов
                    phone_list = contact.get("phone", [])
                    if phone_list is not None:  # Проверка на None
                        for phone in phone_list:
                            await db.execute(
                                "INSERT INTO other_contact_phones (contact_id, phone) VALUES (?, ?)",
                                (contact_id, phone),
                            )

                    email_list = contact.get("email", [])
                    if email_list is not None:  # Проверка на None
                        for email in email_list:
                            await db.execute(
                                "INSERT INTO other_contact_emails (contact_id, email) VALUES (?, ?)",
                                (contact_id, email),
                            )

            # Вставляем данные продуктов
            products_list = order_data.get("products", [])
            if products_list is not None:  # Проверка на None
                for product in products_list:
                    await db.execute(
                        """
                    INSERT INTO products (
                        order_id, amount, percentCommission, preSale, productId, price, stockId,
                        costPrice, discount, description, commission, percentDiscount,
                        parameter, text, barcode, documentName, manufacturer, sku, uktzed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            order_id,
                            product.get("amount"),
                            product.get("percentCommission"),
                            product.get("preSale"),
                            product.get("productId"),
                            product.get("price"),
                            product.get("stockId"),
                            product.get("costPrice"),
                            product.get("discount"),
                            product.get("description"),
                            product.get("commission"),
                            product.get("percentDiscount"),
                            product.get("parameter"),
                            product.get("text"),
                            product.get("barcode"),
                            product.get("documentName"),
                            product.get("manufacturer"),
                            product.get("sku"),
                            product.get("uktzed"),
                        ),
                    )

            # Вставляем tipProdazu1 с заменой числовых значений на текст
            tip_list = order_data.get("tipProdazu1", [])
            if tip_list is not None:  # Проверка на None
                # Получаем соответствие ID -> текст из глобальных метаданных
                tip_mapping = metadata.get("tipProdazu1", {}) if metadata else {}

                for tip in tip_list:
                    # Получаем текстовое представление для числового значения
                    tip_text = tip_mapping.get(
                        tip, str(tip)
                    )  # Если нет в словаре, используем строковое значение

                    await db.execute(
                        "INSERT INTO tip_prodazu (order_id, value) VALUES (?, ?)",
                        (order_id, tip_text),
                    )

            # Вставляем dzereloKomentarVidKlienta
            dzerelo_list = order_data.get("dzereloKomentarVidKlienta", [])
            if dzerelo_list is not None:  # Проверка на None
                for dzerelo in dzerelo_list:
                    await db.execute(
                        "INSERT INTO dzerelo_komentar (order_id, value) VALUES (?, ?)",
                        (order_id, dzerelo),
                    )

            await db.commit()
            # logger.info(f"Заказ с ID {order_id} успешно добавлен в базу данных")
            return True

    except Exception as e:
        logger.error(f"Ошибка при вставке данных заказа: {e}, Заказ {order_id}")
        # Можно добавить более подробную информацию для отладки
        try:
            import traceback

            logger.debug(f"Подробная информация об ошибке: {traceback.format_exc()}")
        except:
            pass
        return False


async def update_order_data(
    db,
    order_id,
    order_data,
    typeId_text,
    statusId_text,
    payment_method_text,
    shipping_method_text,
):
    """Обновление существующего заказа в БД"""
    try:
        # Обновляем основные данные заказа
        await db.execute(
            """
            UPDATE orders SET
                formId = ?, version = ?, organizationId = ?, shipping_method = ?, payment_method = ?,
                shipping_address = ?, comment = ?, timeEntryOrder = ?, holderTime = ?, document_ord_check = ?,
                discountAmount = ?, orderTime = ?, updateAt = ?, statusId = ?, paymentDate = ?, rejectionReason = ?,
                userId = ?, paymentAmount = ?, commissionAmount = ?, costPriceAmount = ?, shipping_costs = ?,
                expensesAmount = ?, profitAmount = ?, typeId = ?, payedAmount = ?, restPay = ?, call = ?, sajt = ?,
                externalId = ?, utmPage = ?, utmMedium = ?, campaignId = ?, utmSourceFull = ?, utmSource = ?,
                utmCampaign = ?, utmContent = ?, utmTerm = ?,uploaded_to_sheets = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                order_data.get("formId"),
                order_data.get("version"),
                order_data.get("organizationId"),
                shipping_method_text,
                payment_method_text,
                order_data.get("shipping_address"),
                order_data.get("comment"),
                order_data.get("timeEntryOrder"),
                order_data.get("holderTime"),
                order_data.get("document_ord_check"),
                order_data.get("discountAmount"),
                order_data.get("orderTime"),
                order_data.get("updateAt"),
                statusId_text,
                order_data.get("paymentDate"),
                order_data.get("rejectionReason"),
                order_data.get("userId"),
                order_data.get("paymentAmount"),
                order_data.get("commissionAmount"),
                order_data.get("costPriceAmount"),
                order_data.get("shipping_costs"),
                order_data.get("expensesAmount"),
                order_data.get("profitAmount"),
                typeId_text,
                order_data.get("payedAmount"),
                order_data.get("restPay"),
                order_data.get("call"),
                order_data.get("sajt"),
                order_data.get("externalId"),
                order_data.get("utmPage"),
                order_data.get("utmMedium"),
                order_data.get("campaignId"),
                order_data.get("utmSourceFull"),
                order_data.get("utmSource"),
                order_data.get("utmCampaign"),
                order_data.get("utmContent"),
                order_data.get("utmTerm"),
                order_id,
            ),
        )

        # Удаляем старые связанные данные
        await db.execute("DELETE FROM delivery_data WHERE order_id = ?", (order_id,))
        await db.execute("DELETE FROM products WHERE order_id = ?", (order_id,))
        await db.execute("DELETE FROM tip_prodazu WHERE order_id = ?", (order_id,))
        await db.execute("DELETE FROM dzerelo_komentar WHERE order_id = ?", (order_id,))
        # Вставляем данные о доставке
        ord_delivery_data = order_data.get("ord_delivery_data", [])
        if ord_delivery_data is not None:  # Проверка на None
            for delivery in ord_delivery_data:
                await db.execute(
                    """
                INSERT INTO delivery_data (
                    order_id, senderId, backDelivery, cityName, provider, payForDelivery,
                    type, trackingNumber, statusCode, deliveryDateAndTime, idEntity,
                    branchNumber, address
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        order_id,
                        delivery.get("senderId"),
                        delivery.get("backDelivery"),
                        delivery.get("cityName"),
                        delivery.get("provider"),
                        delivery.get("payForDelivery"),
                        delivery.get("type"),
                        delivery.get("trackingNumber"),
                        delivery.get("statusCode"),
                        delivery.get("deliveryDateAndTime"),
                        delivery.get("idEntity"),
                        delivery.get("branchNumber"),
                        delivery.get("address"),
                    ),
                )

            # Вставляем данные первичного контакта
            primary_contact = order_data.get("primaryContact")
            if primary_contact:
                contact_id = primary_contact.get("id")

                # Проверяем, существует ли контакт с таким ID
                cursor = await db.execute(
                    "SELECT id FROM primary_contacts WHERE id = ?", (contact_id,)
                )
                existing_contact = await cursor.fetchone()

                if not existing_contact:
                    # Вставляем только если контакта еще нет
                    await db.execute(
                        """
                    INSERT INTO primary_contacts (
                        id, order_id, formId, version, active, con_uGC, con_bloger,
                        lName, fName, mName, telegram, instagramNick, counterpartyId,
                        comment, userId, createTime, leadsCount, leadsSalesCount,
                        leadsSalesAmount, company, con_povnaOplata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            contact_id,
                            order_id,
                            primary_contact.get("formId"),
                            primary_contact.get("version"),
                            primary_contact.get("active"),
                            primary_contact.get("con_uGC"),
                            primary_contact.get("con_bloger"),
                            primary_contact.get("lName"),
                            primary_contact.get("fName"),
                            primary_contact.get("mName"),
                            primary_contact.get("telegram"),
                            primary_contact.get("instagramNick"),
                            primary_contact.get("counterpartyId"),
                            primary_contact.get("comment"),
                            primary_contact.get("userId"),
                            primary_contact.get("createTime"),
                            primary_contact.get("leadsCount"),
                            primary_contact.get("leadsSalesCount"),
                            primary_contact.get("leadsSalesAmount"),
                            primary_contact.get("company"),
                            primary_contact.get("con_povnaOplata"),
                        ),
                    )
                # else:
                #     logger.info(
                #         f"Контакт с ID {contact_id} уже существует в базе данных"
                #     )

                # Вставляем телефоны и email первичного контакта
                phone_list = primary_contact.get("phone", [])
                if phone_list is not None:  # Проверка на None
                    for phone in phone_list:
                        await db.execute(
                            "INSERT INTO contact_phones (contact_id, phone) VALUES (?, ?)",
                            (contact_id, phone),
                        )

                email_list = primary_contact.get("email", [])
                if email_list is not None:  # Проверка на None
                    for email in email_list:
                        await db.execute(
                            "INSERT INTO contact_emails (contact_id, email) VALUES (?, ?)",
                            (contact_id, email),
                        )

            # Вставляем данные других контактов
            contacts_list = order_data.get("contacts", [])
            if contacts_list is not None:  # Проверка на None
                for contact in contacts_list:
                    contact_id = contact.get("id")

                    # Проверяем, существует ли контакт с таким ID
                    cursor = await db.execute(
                        "SELECT id FROM contacts WHERE id = ?", (contact_id,)
                    )
                    existing_contact = await cursor.fetchone()

                    if not existing_contact:
                        # Вставляем только если контакта еще нет
                        await db.execute(
                            """
                        INSERT INTO contacts (
                            id, order_id, formId, version, active, con_uGC, con_bloger,
                            lName, fName, mName, telegram, instagramNick, counterpartyId,
                            comment, userId, createTime, leadsCount, leadsSalesCount,
                            leadsSalesAmount, company, con_povnaOplata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                contact_id,
                                order_id,
                                contact.get("formId"),
                                contact.get("version"),
                                contact.get("active"),
                                contact.get("con_uGC"),
                                contact.get("con_bloger"),
                                contact.get("lName"),
                                contact.get("fName"),
                                contact.get("mName"),
                                contact.get("telegram"),
                                contact.get("instagramNick"),
                                contact.get("counterpartyId"),
                                contact.get("comment"),
                                contact.get("userId"),
                                contact.get("createTime"),
                                contact.get("leadsCount"),
                                contact.get("leadsSalesCount"),
                                contact.get("leadsSalesAmount"),
                                contact.get("company"),
                                contact.get("con_povnaOplata"),
                            ),
                        )
                    # else:
                    #     logger.info(
                    #         f"Контакт с ID {contact_id} уже существует в таблице contacts"
                    #     )

                    # Вставляем телефоны и email других контактов
                    phone_list = contact.get("phone", [])
                    if phone_list is not None:  # Проверка на None
                        for phone in phone_list:
                            await db.execute(
                                "INSERT INTO other_contact_phones (contact_id, phone) VALUES (?, ?)",
                                (contact_id, phone),
                            )

                    email_list = contact.get("email", [])
                    if email_list is not None:  # Проверка на None
                        for email in email_list:
                            await db.execute(
                                "INSERT INTO other_contact_emails (contact_id, email) VALUES (?, ?)",
                                (contact_id, email),
                            )

            # Вставляем данные продуктов
            products_list = order_data.get("products", [])
            if products_list is not None:  # Проверка на None
                for product in products_list:
                    await db.execute(
                        """
                    INSERT INTO products (
                        order_id, amount, percentCommission, preSale, productId, price, stockId,
                        costPrice, discount, description, commission, percentDiscount,
                        parameter, text, barcode, documentName, manufacturer, sku, uktzed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            order_id,
                            product.get("amount"),
                            product.get("percentCommission"),
                            product.get("preSale"),
                            product.get("productId"),
                            product.get("price"),
                            product.get("stockId"),
                            product.get("costPrice"),
                            product.get("discount"),
                            product.get("description"),
                            product.get("commission"),
                            product.get("percentDiscount"),
                            product.get("parameter"),
                            product.get("text"),
                            product.get("barcode"),
                            product.get("documentName"),
                            product.get("manufacturer"),
                            product.get("sku"),
                            product.get("uktzed"),
                        ),
                    )

            # Вставляем tipProdazu1 с заменой числовых значений на текст
            tip_list = order_data.get("tipProdazu1", [])
            if tip_list is not None:  # Проверка на None
                # Получаем соответствие ID -> текст из глобальных метаданных
                tip_mapping = metadata.get("tipProdazu1", {}) if metadata else {}

                for tip in tip_list:
                    # Получаем текстовое представление для числового значения
                    tip_text = tip_mapping.get(
                        tip, str(tip)
                    )  # Если нет в словаре, используем строковое значение

                    await db.execute(
                        "INSERT INTO tip_prodazu (order_id, value) VALUES (?, ?)",
                        (order_id, tip_text),
                    )

            # Вставляем dzereloKomentarVidKlienta
            dzerelo_list = order_data.get("dzereloKomentarVidKlienta", [])
            if dzerelo_list is not None:  # Проверка на None
                for dzerelo in dzerelo_list:
                    await db.execute(
                        "INSERT INTO dzerelo_komentar (order_id, value) VALUES (?, ?)",
                        (order_id, dzerelo),
                    )

            await db.commit()
            # logger.info(f"Заказ с ID {order_id} успешно добавлен в базу данных")
            return True

    except Exception as e:
        logger.error(f"Ошибка при вставке данных заказа: {e}, Заказ {order_id}")
        # Можно добавить более подробную информацию для отладки
        try:
            import traceback

            logger.debug(f"Подробная информация об ошибке: {traceback.format_exc()}")
        except:
            pass
        return False

    # Не удаляем contacts, contact_phones, contact_emails и т.д. -
    # это может требовать более сложной логики в зависимости от ваших потребностей

    # Вставляем новые связанные данные
    # (здесь нужно перенести соответствующий код из вашей функции insert_order_data)

    logger.info(f"Заказ с ID {order_id} успешно обновлен в базе данных")


async def insert_or_update_order_data(order_data):
    """Вставка или обновление данных заказа в БД в зависимости от статуса"""
    order_id = None

    try:
        order_id = order_data.get("id")
        if not order_id:
            logger.info("Ошибка: отсутствует ID заказа в данных")
            return False

        # Получаем текстовое представление для statusId из JSON
        statusId = order_data.get("statusId")
        statusId_text = str(statusId)

        if statusId is not None:
            # Получаем соответствие ID -> текст из глобальных метаданных
            global metadata
            if metadata and "statusId" in metadata:
                status_mapping = metadata["statusId"]
                statusId_text = status_mapping.get(statusId, str(statusId))

        # Получаем текстовое представление для typeId
        typeId = order_data.get("typeId")
        typeId_text = str(typeId)
        if typeId is not None:
            # Получаем соответствие ID -> текст из глобальных метаданных
            if metadata and "typeId" in metadata:
                type_mapping = metadata["typeId"]
                typeId_text = type_mapping.get(typeId, str(typeId))

        # shipping_method ID Переводим в текст
        shipping_method = order_data.get("shipping_method")
        shipping_method_text = str(shipping_method)

        if shipping_method is not None:
            # Получаем соответствие ID -> текст из глобальных метаданных
            if metadata and "shipping_method" in metadata:
                type_mapping = metadata["shipping_method"]
                shipping_method_text = type_mapping.get(
                    shipping_method, str(shipping_method)
                )

        # payment_method ID Переводим в текст
        payment_method = order_data.get("payment_method")
        payment_method_text = str(payment_method)

        if payment_method is not None:
            # Получаем соответствие ID -> текст из глобальных метаданных
            if metadata and "payment_method" in metadata:
                type_mapping = metadata["payment_method"]
                payment_method_text = type_mapping.get(
                    payment_method, str(payment_method)
                )

        # Список статусов, при которых заказ можно обновлять
        updatable_statuses = [
            "Новий",
            "Підтверджено",
            "На відправку",
            "Відправлено",
            "Сплачено",
        ]

        # Список конечных статусов, при которых заказ больше не обновляется
        final_statuses = ["Продаж", "Відмова", "Повернення", "Видалений"]

        async with aiosqlite.connect(DB_PATH) as db:
            # Проверяем, существует ли уже запись с таким ID
            cursor = await db.execute(
                "SELECT id, statusId FROM orders WHERE id = ?", (order_id,)
            )
            existing_record = await cursor.fetchone()

            if existing_record:
                # Заказ уже существует
                existing_status = existing_record[1]
                existing_status_text = str(existing_status)

                # Проверяем, есть ли соответствие для существующего статуса
                if metadata and "statusId" in metadata:
                    status_mapping = metadata["statusId"]
                    existing_status_text = status_mapping.get(
                        existing_status, str(existing_status)
                    )

                # Проверяем условия обновления
                should_update = False

                # Условие 1: Если текущий статус в БД находится в списке обновляемых
                if existing_status_text in updatable_statuses:
                    # Проверяем, не пытаемся ли мы обновить на тот же статус
                    if existing_status_text != statusId_text:
                        should_update = True
                        logger.info(
                            f"Обновляем заказ: статус изменился с '{existing_status_text}' на '{statusId_text}'"
                        )
                    # else:
                    #     logger.info(
                    #         f"Статус не изменился: '{existing_status_text}' -> '{statusId_text}'. Пропускаем обновление."
                    #     )

                # Условие 2: Если текущий статус в БД является конечным
                elif existing_status_text in final_statuses:
                    logger.info(
                        f"Заказ с ID {order_id} имеет конечный статус '{existing_status_text}'. Обновление не требуется."
                    )
                    should_update = False

                # Условие 3: Для всех других случаев (на всякий случай)
                else:
                    logger.info(
                        f"Заказ с ID {order_id} имеет неизвестный статус '{existing_status_text}'. Обновляем на '{statusId_text}'."
                    )
                    should_update = True

                if should_update:
                    logger.info(
                        f"Обновляем заказ с ID {order_id} (статус: {existing_status_text} -> {statusId_text})"
                    )
                    await update_order_data(
                        db,
                        order_id,
                        order_data,
                        typeId_text,
                        statusId_text,
                        payment_method_text,
                        shipping_method_text,
                    )
                    return True
                else:
                    return False
            else:
                # Заказ не существует, вставляем новую запись
                logger.info(f"Новый заказ с ID {order_id}, статус: {statusId_text}")
                await insert_order_data(
                    db,
                    order_id,
                    order_data,
                    typeId_text,
                    statusId_text,
                    payment_method_text,
                    shipping_method_text,
                )
                return True

    except Exception as e:
        logger.error(
            f"Ошибка при вставке/обновлении данных заказа: {e}, Заказ {order_id}"
        )
        try:
            import traceback

            logger.debug(f"Подробная информация об ошибке: {traceback.format_exc()}")
        except:
            pass
        return False


async def get_non_uploaded_orders() -> List[Dict[str, Any]]:
    """Получение всех заказов, которые еще не были выгружены в Google Sheets"""
    orders = []

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, order_data FROM orders WHERE uploaded_to_sheets = FALSE"
        )
        rows = await cursor.fetchall()

        for row in rows:
            order_data = json.loads(row["order_data"])
            orders.append({"id": row["id"], "data": order_data})

    return orders


async def mark_as_uploaded(order_id: int):
    """Отметить заказ как выгруженный в Google Sheets"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE orders SET uploaded_to_sheets = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (order_id,),
        )
        await db.commit()
        logger.info(f"Заказ с ID {order_id} отмечен как выгруженный")


async def process_order(file_path: str):
    """Обработка JSON файла и загрузка данных в БД"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Загружаем весь файл в переменную
            content = f.read().strip()

            # Загружаем метаданные из файла
            json_data = json.loads(content)
            global metadata
            metadata = load_metadata_from_json(json_data)
            # logger.info(f"Метаданные загружены: {metadata}")

            # Проверяем, содержит ли JSON ключ "data" с массивом заказов
            if (
                isinstance(json_data, dict)
                and "data" in json_data
                and isinstance(json_data["data"], list)
            ):
                orders = json_data["data"]
                # logger.info(f"Найден массив 'data' с {len(orders)} заказами")
                for order in orders:
                    await insert_or_update_order_data(order)
                return

            # Если это не объект с ключом "data", продолжаем обработку
            if isinstance(json_data, list):
                # Это массив заказов
                logger.info(f"Обрабатываем массив из {len(json_data)} заказов")
                for order in json_data:
                    await insert_or_update_order_data(order)
            elif isinstance(json_data, dict):
                # Это один заказ
                logger.info("Обрабатываем одиночный заказ")
                await insert_or_update_order_data(json_data)
            else:
                logger.error(f"Неподдерживаемый формат данных в файле: {file_path}")

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
    except Exception as e:
        logger.error(f"Ошибка при обработке файла {file_path}: {e}")
        import traceback

        logger.error(traceback.format_exc())


async def get_all_order_data():
    """Получить полные данные о заказах с объединением всех связанных таблиц"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Основные данные заказов
        query = """
        SELECT o.* FROM orders o WHERE o.uploaded_to_sheets = FALSE
        """

        cursor = await db.execute(query)
        orders = await cursor.fetchall()

        if not orders:
            logger.error("Нет новых заказов для выгрузки")
            return []

        # Преобразуем данные в список словарей с объединением всех связанных таблиц
        result = []

        for order in orders:
            order_dict = dict(order)
            order_id = order_dict["id"]

            # 1. Добавляем данные о доставке
            delivery_query = "SELECT * FROM delivery_data WHERE order_id = ?"
            cursor = await db.execute(delivery_query, (order_id,))
            deliveries = await cursor.fetchall()

            if deliveries:
                delivery = dict(deliveries[0])
                # Добавляем префикс, чтобы избежать конфликтов имен полей
                for key, value in delivery.items():
                    if key != "order_id" and key != "id":  # Исключаем лишние поля
                        order_dict[f"delivery_{key}"] = value

            # 2. Добавляем данные о первичном контакте
            contact_query = "SELECT * FROM primary_contacts WHERE order_id = ?"
            cursor = await db.execute(contact_query, (order_id,))
            contacts = await cursor.fetchall()

            if contacts:
                contact = dict(contacts[0])
                contact_id = contact.get("id")

                # Добавляем данные контакта с префиксом
                for key, value in contact.items():
                    if key != "order_id" and key != "id":
                        order_dict[f"contact_{key}"] = value

                # Добавляем телефоны контакта
                phones_query = "SELECT phone FROM contact_phones WHERE contact_id = ?"
                cursor = await db.execute(phones_query, (contact_id,))
                phones = await cursor.fetchall()

                # Объединяем телефоны в одну строку с разделителем
                phone_list = [row[0] for row in phones]
                order_dict["contact_phones"] = (
                    "; ".join(phone_list) if phone_list else ""
                )

                # Добавляем email контакта
                emails_query = "SELECT email FROM contact_emails WHERE contact_id = ?"
                cursor = await db.execute(emails_query, (contact_id,))
                emails = await cursor.fetchall()

                # Объединяем email в одну строку с разделителем
                email_list = [row[0] for row in emails]
                order_dict["contact_emails"] = (
                    "; ".join(email_list) if email_list else ""
                )

            # 3. Добавляем данные о других контактах (в случае если они есть)
            other_contacts_query = "SELECT * FROM contacts WHERE order_id = ?"
            cursor = await db.execute(other_contacts_query, (order_id,))
            other_contacts = await cursor.fetchall()

            if other_contacts:
                # Объединяем информацию о других контактах в одну строку
                contacts_info = []
                for i, other_contact in enumerate(other_contacts, 1):
                    oc_dict = dict(other_contact)
                    oc_id = oc_dict.get("id")

                    # Получаем телефоны другого контакта
                    oc_phones_query = (
                        "SELECT phone FROM other_contact_phones WHERE contact_id = ?"
                    )
                    cursor = await db.execute(oc_phones_query, (oc_id,))
                    oc_phones = await cursor.fetchall()
                    oc_phone_list = [row[0] for row in oc_phones]

                    # Получаем emails другого контакта
                    oc_emails_query = (
                        "SELECT email FROM other_contact_emails WHERE contact_id = ?"
                    )
                    cursor = await db.execute(oc_emails_query, (oc_id,))
                    oc_emails = await cursor.fetchall()
                    oc_email_list = [row[0] for row in oc_emails]

                    # Формируем строку с информацией о контакте
                    contact_str = f"{oc_dict.get('lName')} {oc_dict.get('fName')}"
                    if oc_phone_list:
                        contact_str += f", тел: {'; '.join(oc_phone_list)}"
                    if oc_email_list:
                        contact_str += f", email: {'; '.join(oc_email_list)}"

                    contacts_info.append(contact_str)

                order_dict["other_contacts"] = " | ".join(contacts_info)

            # 4. Добавляем данные о продуктах
            products_query = "SELECT * FROM products WHERE order_id = ?"
            cursor = await db.execute(products_query, (order_id,))
            products = await cursor.fetchall()

            if products:
                # Объединяем информацию о продуктах в одну строку
                products_info = []
                for product in products:
                    p_dict = dict(product)
                    name_product = p_dict.get("text")
                    amount_product = p_dict.get("amount")
                    price_product = p_dict.get("price")
                    discount_product = p_dict.get("discount")
                    all_data_product = {
                        "name_product": name_product,
                        "amount_product": amount_product,
                        "price_product": price_product,
                        "discount_product": discount_product,
                    }
                    # Формируем строку с информацией о продукте
                    product_str = f"{p_dict.get('text')} (кол-во: {p_dict.get('amount')}, цена: {p_dict.get('price')})"
                    products_info.append(all_data_product)

                order_dict["products_info"] = products_info
                # order_dict["products_info"] = " | ".join(products_info)

            # 5. Добавляем данные о типах продаж
            tip_query = "SELECT value FROM tip_prodazu WHERE order_id = ?"
            cursor = await db.execute(tip_query, (order_id,))
            tips = await cursor.fetchall()

            if tips:
                tip_list = [str(row[0]) for row in tips]
                order_dict["tip_prodazu_values"] = "; ".join(tip_list)

            # 6. Добавляем данные о комментариях клиентов
            dzerelo_query = "SELECT value FROM dzerelo_komentar WHERE order_id = ?"
            cursor = await db.execute(dzerelo_query, (order_id,))
            dzerelo = await cursor.fetchall()

            if dzerelo:
                dzerelo_list = [row[0] for row in dzerelo]
                order_dict["client_comments"] = "; ".join(dzerelo_list)

            result.append(order_dict)

        return result


async def mark_orders_as_uploaded(order_ids):
    """Отметить заказы как выгруженные в Google Sheets"""
    if not order_ids:
        return

    placeholders = ",".join(["?"] * len(order_ids))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE orders SET uploaded_to_sheets = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})",
            order_ids,
        )
        await db.commit()
        logger.info(
            f"Заказы с ID {', '.join(map(str, order_ids))} отмечены как выгруженные"
        )


def connect_to_google_sheets():
    """Подключение к Google Sheets API"""
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        # Проверяем существование файла с учетными данными
        if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
            logger.error(
                f"Файл с учетными данными Google не найден: {GOOGLE_CREDENTIALS_PATH}"
            )
            return None

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            GOOGLE_CREDENTIALS_PATH, scope
        )
        client = gspread.authorize(creds)

        # Открываем таблицу по ID
        spreadsheet = client.open_by_key(
            SPREADSHEET_ID
        )  # Используем open_by_key вместо open_by_id
        return spreadsheet

    except FileNotFoundError as e:
        logger.error(f"Не удалось найти файл учетных данных: {e}")
        return None
    except gspread.exceptions.GSpreadException as e:
        logger.error(f"Ошибка Google Sheets API: {e}")
        return None
    except Exception as e:
        logger.error(f"Неизвестная ошибка при подключении к Google Sheets: {e}")
        return None


def prepare_sheet(spreadsheet, sheet_name, headers):
    """Подготовка листа: создание, если не существует, и добавление заголовков"""
    # Проверяем, существует ли лист
    try:
        worksheet = spreadsheet.worksheet(sheet_name)

    except gspread.exceptions.WorksheetNotFound:
        # Если лист не существует, создаем его
        worksheet = spreadsheet.add_worksheet(
            title=sheet_name, rows=1000, cols=len(headers)
        )

    # Проверяем заголовки
    try:
        existing_headers = worksheet.row_values(1)
        if not existing_headers:
            # Если заголовки отсутствуют, добавляем их
            worksheet.append_row(headers)
        elif len(existing_headers) < len(headers):
            # Если количество заголовков изменилось, обновляем их полностью
            for col, header in enumerate(headers, start=1):
                worksheet.update_cell(1, col, header)
        elif existing_headers != headers:
            # Если заголовки отличаются, обновляем только те, которые изменились
            for col, (old, new) in enumerate(zip(existing_headers, headers), start=1):
                if old != new:
                    worksheet.update_cell(1, col, new)
    except Exception as e:
        logger.error(f"Ошибка при проверке заголовков: {e}")
        # Если что-то пошло не так, просто добавляем заголовки
        worksheet.append_row(headers)

    return worksheet


def get_next_empty_row(worksheet):
    """Находим индекс следующей пустой строки"""
    # Получаем все значения в первом столбце
    col_values = worksheet.col_values(1)

    # Длина списка значений + 1 (учитывая, что нумерация строк начинается с 1)
    # Если у нас только заголовки, вернется 2 (строка сразу после заголовков)
    return len(col_values) + 1


def upload_data_to_sheet(worksheet, data):
    """Выгрузка данных в лист"""
    if not data:
        logger.error(f"Нет данных для выгрузки в лист {worksheet.title}")
        return

    # Находим следующую пустую строку
    next_row = get_next_empty_row(worksheet)
    logger.info(f"Следующая пустая строка: {next_row}")

    # Получаем заголовки
    headers = worksheet.row_values(1)

    # Подготавливаем строки для добавления
    rows_to_append = []
    for item in data:
        # Создаем строку данных в соответствии с порядком заголовков
        row = []
        for header in headers:
            # Ищем соответствующее поле в данных (прямое соответствие)
            if header in item:
                value = item[header]
            else:
                # Если прямого соответствия нет, пробуем найти по нижнему регистру
                found = False
                for key, val in item.items():
                    if key.lower() == header.lower():
                        value = val
                        found = True
                        break

                if not found:
                    value = ""  # Если поле не найдено

            # Преобразуем None в пустую строку
            if value is None:
                value = ""
            # Преобразуем сложные типы данных в строки
            elif isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)

            row.append(value)

        rows_to_append.append(row)

    # Добавляем данные пакетом для оптимизации
    if rows_to_append:
        worksheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")

    logger.info(f"Выгружено {len(rows_to_append)} строк в лист {worksheet.title}")

    return len(rows_to_append)


async def export_orders_to_sheets():
    """Экспорт объединенных данных о заказах в Google Sheets"""
    try:
        logger.info("Начинаем экспорт данных в Google Sheets...")

        # Получаем объединенные данные о заказах
        orders_data = await get_all_order_data()
        if not orders_data:
            logger.error("Нет новых заказов для выгрузки")
            return

        # Подключаемся к Google Sheets
        spreadsheet = connect_to_google_sheets()
        if not spreadsheet:
            logger.error("Не удалось подключиться к Google Sheets")
            return

        # Получаем ID строк из колонки A
        all_ids_line = get_ids_from_column_a(spreadsheet, SHEET_NAME)

        try:
            # Проверяем, существует ли лист
            worksheet = spreadsheet.worksheet(SHEET_NAME)

            # Получаем существующие заголовки из таблицы
            existing_headers = worksheet.row_values(1)

            if not existing_headers:
                # Если заголовков нет, создаем их из данных заказов
                logger.info("Заголовки в таблице отсутствуют, создаем новые")

                # Создаем полный список заголовков из всех возможных полей
                all_headers = set()
                for order in orders_data:
                    for key in order.keys():
                        all_headers.add(key)

                # Сортируем заголовки для лучшей читаемости (основные поля заказа в начале)
                headers = []

                # Сначала добавляем основные поля заказа
                base_fields = [
                    "id",
                    "formId",
                    "version",
                    "orderTime",
                    "statusId",
                    "paymentAmount",
                ]
                for field in base_fields:
                    if field in all_headers:
                        headers.append(field)
                        all_headers.remove(field)

                # Затем добавляем поля контакта
                contact_fields = [h for h in all_headers if h.startswith("contact_")]
                for field in sorted(contact_fields):
                    headers.append(field)
                    all_headers.remove(field)

                # Затем поля доставки
                delivery_fields = [h for h in all_headers if h.startswith("delivery_")]
                for field in sorted(delivery_fields):
                    headers.append(field)
                    all_headers.remove(field)

                # Затем специальные поля продуктов и комментариев
                special_fields = [
                    "products_info",
                    "other_contacts",
                    "tip_prodazu_values",
                    "client_comments",
                    "orderTimeLook",
                ]
                for field in special_fields:
                    if field in all_headers:
                        headers.append(field)
                        all_headers.remove(field)

                # Добавляем оставшиеся поля в алфавитном порядке
                for field in sorted(all_headers):
                    headers.append(field)

                # Добавляем заголовки в первую строку
                worksheet.append_row(headers)
            else:
                headers = existing_headers

        except gspread.exceptions.WorksheetNotFound:
            # Если лист не существует, создаем его
            logger.info(f"Лист {SHEET_NAME} не найден, создаем новый")

            # Создаем полный список заголовков из всех возможных полей
            all_headers = set()
            for order in orders_data:
                for key in order.keys():
                    all_headers.add(key)

            # Сортируем заголовки (аналогично коду выше)
            headers = []
            base_fields = [
                "id",
                "formId",
                "version",
                "orderTime",
                "statusId",
                "paymentAmount",
            ]
            for field in base_fields:
                if field in all_headers:
                    headers.append(field)
                    all_headers.remove(field)

            contact_fields = [h for h in all_headers if h.startswith("contact_")]
            for field in sorted(contact_fields):
                headers.append(field)
                all_headers.remove(field)

            delivery_fields = [h for h in all_headers if h.startswith("delivery_")]
            for field in sorted(delivery_fields):
                headers.append(field)
                all_headers.remove(field)

            special_fields = [
                "products_info",
                "other_contacts",
                "tip_prodazu_values",
                "client_comments",
                "orderTimeLook",
            ]
            for field in special_fields:
                if field in all_headers:
                    headers.append(field)
                    all_headers.remove(field)

            for field in sorted(all_headers):
                headers.append(field)

            # Создаем новый лист
            worksheet = spreadsheet.add_worksheet(
                title=SHEET_NAME, rows=1000, cols=len(headers)
            )

            # Добавляем заголовки
            worksheet.append_row(headers)

            # Обновляем список ID строк (пока пустой)
            all_ids_line = []

        # Логируем информацию о заголовках и данных для отладки
        # Выгружаем данные
        update_orders_in_sheet(worksheet, orders_data, all_ids_line)

        # Отмечаем заказы как выгруженные
        order_ids = [order["id"] for order in orders_data]
        await mark_orders_as_uploaded(order_ids)

        logger.info("Экспорт данных в Google Sheets завершен")

    except Exception as e:
        logger.error(f"Ошибка при экспорте данных в Google Sheets: {e}")
        import traceback

        logger.error(traceback.format_exc())


async def update_order_time_look_for_existing_orders():
    """
    Одноразовая функция для заполнения поля orderTimeLook для всех существующих заказов
    на основе значений в поле orderTime
    """
    try:
        logger.info(
            "Начинаем обновление поля orderTimeLook для существующих заказов..."
        )

        async with aiosqlite.connect(DB_PATH) as db:
            # Получаем все записи с непустым orderTime
            cursor = await db.execute(
                "SELECT id, orderTime FROM orders WHERE orderTime IS NOT NULL"
            )
            orders = await cursor.fetchall()

            if not orders:
                logger.info("Нет заказов для обновления")
                return

            logger.info(f"Найдено {len(orders)} заказов для обновления")
            updated_count = 0
            error_count = 0

            for order in orders:
                order_id, order_time = order

                try:
                    if order_time:
                        # Парсим дату из строки формата "2024-08-03 09:22:04"
                        dt = datetime.strptime(order_time, "%Y-%m-%d %H:%M:%S")
                        # Форматируем в нужный формат "08.2024"
                        order_time_look = dt.strftime("%m.%Y")

                        # Обновляем запись
                        await db.execute(
                            "UPDATE orders SET orderTimeLook = ? WHERE id = ?",
                            (order_time_look, order_id),
                        )
                        updated_count += 1

                        # Выводим прогресс каждые 100 записей
                        if updated_count % 100 == 0:
                            logger.info(f"Обновлено {updated_count} заказов...")
                except Exception as e:
                    logger.error(f"Ошибка при обновлении заказа ID {order_id}: {e}")
                    error_count += 1

            # Сохраняем изменения
            await db.commit()

            logger.info(
                f"Обновление завершено. Успешно обновлено: {updated_count}, с ошибками: {error_count}"
            )

    except Exception as e:
        logger.error(f"Ошибка при массовом обновлении поля orderTimeLook: {e}")
        try:
            import traceback

            logger.debug(f"Подробная информация об ошибке: {traceback.format_exc()}")
        except:
            pass


def update_orders_in_sheet(worksheet, orders_data, all_ids_line):
    """
    Обновляет или добавляет данные о заказах в Google Sheets с точным соответствием заголовкам.
    Добавлены паузы между запросами для соблюдения ограничений API Google Sheets.
    """
    try:
        # Получаем заголовки листа (первая строка)
        headers = worksheet.row_values(1)
        if not headers:
            logger.error("Заголовки листа не найдены.")
            return

        # Проверяем наличие заголовка orderTimeLook
        if "orderTimeLook" not in headers:
            # Добавляем новый заголовок в конец
            next_col = len(headers) + 1
            cell = rowcol_to_a1(1, next_col)

            # Добавляем паузу перед добавлением нового заголовка
            time.sleep(1)

            worksheet.update(cell, "orderTimeLook")
            logger.info(f"Добавлен заголовок 'orderTimeLook' в ячейку {cell}")

            # Обновляем список заголовков
            headers.append("orderTimeLook")

        # Удаляем дублирующиеся заголовки, если они есть
        unique_headers = []
        seen_headers = set()
        for header in headers:
            if header not in seen_headers:
                seen_headers.add(header)
                unique_headers.append(header)

        # Если были найдены дубликаты, логируем это
        if len(unique_headers) != len(headers):
            logger.warning(
                f"Найдены дублирующиеся заголовки в таблице: {len(headers) - len(unique_headers)}"
            )
            logger.info(f"Уникальные заголовки: {unique_headers}")

        # Счетчик запросов для отслеживания и предотвращения превышения лимитов
        request_count = 0
        for order in orders_data:
            order_id_str = str(order.get("id", ""))
            # Поиск строки с совпадающим ID
            target_row = None
            for row_num, id_val in all_ids_line:
                if id_val == order_id_str:
                    target_row = row_num
                    break

            # Логируем данные заказа для отладки
            logger.info(f"Обрабатываем заказ ID {order_id_str}")

            # Если нашли строку, сначала получим текущие значения для отладки
            if target_row is not None:
                logger.info(f"Найдена существующая строка {target_row}")
                try:
                    current_values = worksheet.row_values(target_row)
                    # logger.info(f"Текущие значения строки: {current_values}")
                except Exception as e:
                    logger.warning(f"Не удалось получить текущие значения строки: {e}")

            # Создаем словарь для удобного доступа к данным по заголовкам
            row_data_by_header = {}

            # Проходим по всем заголовкам и ищем соответствующие данные
            for header in unique_headers:
                # Сначала пробуем прямое совпадение
                if header in order:
                    row_data_by_header[header] = order[header]
                    continue

                # Если прямого совпадения нет, ищем без учета регистра
                header_lower = header.lower()
                found = False
                for key, value in order.items():
                    if key.lower() == header_lower:
                        row_data_by_header[header] = value
                        found = True
                        break

                # Если по-прежнему не нашли, устанавливаем пустое значение
                if not found:
                    row_data_by_header[header] = ""

            # Преобразование значений
            for header, value in row_data_by_header.items():
                if value is None:
                    row_data_by_header[header] = ""
                elif isinstance(value, (dict, list)):
                    row_data_by_header[header] = json.dumps(value, ensure_ascii=False)

            # Логируем подготовленные данные
            # logger.info(f"Подготовленные данные по заголовкам: {row_data_by_header}")

            if target_row is not None:
                # Обновляем существующую строку по одной ячейке за раз
                for col_idx, header in enumerate(unique_headers, start=1):
                    try:
                        value = row_data_by_header.get(header, "")
                        # Обновляем ячейку
                        worksheet.update_cell(target_row, col_idx, value)

                        # Увеличиваем счетчик запросов
                        request_count += 1

                        # Делаем небольшую паузу между обновлениями ячеек
                        time.sleep(0.5)

                        # Более длинная пауза после каждых 10 запросов
                        if request_count % 10 == 0:
                            logger.info(
                                "Пауза для соблюдения лимитов API (3 секунда)..."
                            )
                            time.sleep(3)
                    except Exception as cell_err:
                        logger.error(
                            f"Ошибка при обновлении ячейки ({target_row}, {col_idx}) = {header}: {cell_err}"
                        )
                        # При ошибке делаем более длинную паузу
                        time.sleep(5)

                logger.info(
                    f"Завершено обновление строки {target_row} для заказа с id {order_id_str}"
                )

                # Пауза после обработки каждого заказа
                time.sleep(2)

            else:
                # Добавляем новую строку

                # Формируем строку данных в том же порядке, что и заголовки
                new_row_data = [
                    row_data_by_header.get(header, "") for header in unique_headers
                ]

                try:
                    # Делаем длинную паузу перед добавлением новой строки
                    time.sleep(3)
                    worksheet.append_row(
                        new_row_data, value_input_option="USER_ENTERED"
                    )
                    logger.info(
                        f"Добавлена новая строка для заказа с id {order_id_str}"
                    )

                    # Пауза после добавления строки
                    time.sleep(3)
                    request_count += 1
                except Exception as append_err:
                    logger.error(f"Ошибка при добавлении новой строки: {append_err}")

                    # В случае ошибки делаем очень длинную паузу и пробуем еще раз
                    logger.info("Делаем паузу на 20 секунд и пробуем снова...")
                    time.sleep(20)
                    try:
                        worksheet.append_row(
                            new_row_data, value_input_option="USER_ENTERED"
                        )
                        logger.info(
                            f"Успешно добавлена новая строка для заказа с id {order_id_str} после повторной попытки"
                        )
                    except Exception as retry_err:
                        logger.error(
                            f"Не удалось добавить новую строку даже после паузы: {retry_err}"
                        )

    except Exception as e:
        logger.error(f"Ошибка при обновлении заказов в Google Sheets: {e}")
        import traceback

        logger.error(traceback.format_exc())


def get_ids_from_column_a(spreadsheet, sheet_name):
    """
    Подключается к Google Sheets, открывает лист SHEET_NAME и возвращает
    список кортежей (номер строки, id), где id берутся из колонки A.
    """
    try:

        worksheet = spreadsheet.worksheet(sheet_name)

        # Получаем все значения из колонки A
        col_a_values = worksheet.col_values(1)

        # Формируем список кортежей: (номер строки, id)
        # Учтите, что первая строка может содержать заголовок.
        result = [(idx, cell) for idx, cell in enumerate(col_a_values, start=1)]
        return result

    except Exception as e:
        logger.error(f"Ошибка при получении значений из колонки A: {e}")
        return []


# async def update_analytics_table():
#     """Создает и обновляет улучшенную аналитическую таблицу продаж с учетом скидок"""
#     try:
#         async with aiosqlite.connect(DB_PATH) as db:
#             # Добавляем поля для скидок в аналитическую таблицу
#             await db.execute(
#                 """
#             CREATE TABLE IF NOT EXISTS sales_analytics (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 order_id INTEGER,
#                 product_id INTEGER,
#                 product_name TEXT,
#                 quantity INTEGER,
#                 price REAL,               -- Исходная цена (без скидки)
#                 discount REAL,            -- Скидка на единицу товара
#                 percent_discount REAL,    -- Процент скидки
#                 price_with_discount REAL, -- Цена с учетом скидки
#                 total_amount REAL,        -- Общая сумма (цена с учетом скидки * количество)
#                 sale_date TEXT,           -- YYYY-MM-DD
#                 day INTEGER,              -- День месяца (1-31)
#                 month INTEGER,            -- Месяц (1-12)
#                 quarter INTEGER,          -- Квартал (1-4)
#                 year INTEGER,             -- Год
#                 month_year TEXT,          -- MM.YYYY
#                 UNIQUE(order_id, product_id)
#             )
#             """
#             )

#             # Получаем заказы, которые еще не обработаны
#             query = """
#             SELECT o.id, o.orderTime
#             FROM orders o
#             WHERE EXISTS (
#                 SELECT 1 FROM products p WHERE p.order_id = o.id
#             )
#             AND NOT EXISTS (
#                 SELECT 1 FROM sales_analytics s WHERE s.order_id = o.id
#             )
#             """

#             cursor = await db.execute(query)
#             orders = await cursor.fetchall()

#             processed_count = 0
#             skipped_count = 0

#             for order in orders:
#                 order_id, order_time = order

#                 # Если нет orderTime, пропускаем
#                 if not order_time:
#                     continue

#                 try:
#                     # Парсим и форматируем дату
#                     dt = datetime.strptime(order_time, "%Y-%m-%d %H:%M:%S")
#                     sale_date = dt.strftime("%Y-%m-%d")
#                     day = dt.day
#                     month = dt.month
#                     year = dt.year

#                     # Вычисляем квартал (1-4)
#                     quarter = (month - 1) // 3 + 1

#                     # Формат месяц.год
#                     month_year = dt.strftime("%m.%Y")
#                 except Exception as e:
#                     logger.error(
#                         f"Ошибка при обработке даты для заказа {order_id}: {e}"
#                     )
#                     continue

#                 # Получаем все товары для этого заказа с учетом поля discount
#                 products_query = """
#                 SELECT productId, text, amount, price, discount, percentDiscount
#                 FROM products
#                 WHERE order_id = ?
#                 """

#                 cursor = await db.execute(products_query, (order_id,))
#                 products = await cursor.fetchall()

#                 for product in products:
#                     (
#                         product_id,
#                         product_name,
#                         quantity,
#                         price,
#                         discount,
#                         percent_discount,
#                     ) = product

#                     # Предотвращаем ошибки с неправильными значениями
#                     if not quantity or quantity <= 0:
#                         quantity = 0
#                     if not price or price <= 0:
#                         price = 0
#                     if not discount or discount < 0:
#                         discount = 0
#                     if not percent_discount or percent_discount < 0:
#                         percent_discount = 0

#                     # Рассчитываем цену с учетом скидки
#                     price_with_discount = price - discount
#                     if price_with_discount < 0:
#                         price_with_discount = 0

#                     # Общая сумма с учетом скидки и количества
#                     total_amount = price_with_discount * quantity

#                     # Вставляем запись в аналитическую таблицу
#                     try:
#                         await db.execute(
#                             """
#                         INSERT OR IGNORE INTO sales_analytics
#                         (order_id, product_id, product_name, quantity, price, discount,
#                          percent_discount, price_with_discount, total_amount,
#                          sale_date, day, month, quarter, year, month_year)
#                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                         """,
#                             (
#                                 order_id,
#                                 product_id,
#                                 product_name,
#                                 quantity,
#                                 price,
#                                 discount,
#                                 percent_discount,
#                                 price_with_discount,
#                                 total_amount,
#                                 sale_date,
#                                 day,
#                                 month,
#                                 quarter,
#                                 year,
#                                 month_year,
#                             ),
#                         )

#                         # Проверяем, была ли вставка успешной
#                         changes = db.total_changes
#                         if changes > 0:
#                             processed_count += 1
#                         else:
#                             skipped_count += 1
#                     except Exception as e:
#                         logger.debug(f"Ошибка при вставке записи: {e}")
#                         skipped_count += 1

#             await db.commit()
#             logger.info(
#                 f"Обновлена аналитическая таблица: добавлено {processed_count} записей, пропущено {skipped_count}"
#             )


#     except Exception as e:
#         logger.error(f"Ошибка при обновлении аналитической таблицы: {e}")
# async def update_analytics_table():
#     """Создает и обновляет улучшенную аналитическую таблицу продаж с учетом скидок и типа продажи"""
#     try:
#         async with aiosqlite.connect(DB_PATH) as db:
#             # Добавляем поля для скидок в аналитическую таблицу и тип продажи
#             await db.execute(
#                 """
#             CREATE TABLE IF NOT EXISTS sales_analytics (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 order_id INTEGER,
#                 product_id INTEGER,
#                 product_name TEXT,
#                 quantity INTEGER,
#                 price REAL,               -- Исходная цена (без скидки)
#                 discount REAL,            -- Скидка на единицу товара
#                 percent_discount REAL,    -- Процент скидки
#                 price_with_discount REAL, -- Цена с учетом скидки
#                 total_amount REAL,        -- Общая сумма (цена с учетом скидки * количество)
#                 sale_date TEXT,           -- YYYY-MM-DD
#                 day INTEGER,              -- День месяца (1-31)
#                 month INTEGER,            -- Месяц (1-12)
#                 quarter INTEGER,          -- Квартал (1-4)
#                 year INTEGER,             -- Год
#                 month_year TEXT,          -- MM.YYYY
#                 tip_prodazu TEXT,         -- Тип продажи
#                 UNIQUE(order_id, product_id)
#             )
#             """
#             )

#             # Получаем заказы, которые еще не обработаны
#             query = """
#             SELECT o.id, o.orderTime
#             FROM orders o
#             WHERE EXISTS (
#                 SELECT 1 FROM products p WHERE p.order_id = o.id
#             )
#             AND NOT EXISTS (
#                 SELECT 1 FROM sales_analytics s WHERE s.order_id = o.id
#             )
#             """

#             cursor = await db.execute(query)
#             orders = await cursor.fetchall()

#             processed_count = 0
#             skipped_count = 0

#             for order in orders:
#                 order_id, order_time = order

#                 # Если нет orderTime, пропускаем
#                 if not order_time:
#                     continue

#                 # Получаем тип продажи для этого заказа
#                 tip_prodazu_query = """
#                 SELECT value
#                 FROM tip_prodazu
#                 WHERE order_id = ?
#                 LIMIT 1
#                 """

#                 cursor_tip = await db.execute(tip_prodazu_query, (order_id,))
#                 tip_row = await cursor_tip.fetchone()
#                 tip_prodazu_value = tip_row[0] if tip_row else None

#                 try:
#                     # Парсим и форматируем дату
#                     dt = datetime.strptime(order_time, "%Y-%m-%d %H:%M:%S")
#                     sale_date = dt.strftime("%Y-%m-%d")
#                     day = dt.day
#                     month = dt.month
#                     year = dt.year

#                     # Вычисляем квартал (1-4)
#                     quarter = (month - 1) // 3 + 1

#                     # Формат месяц.год
#                     month_year = dt.strftime("%m.%Y")
#                 except Exception as e:
#                     logger.error(
#                         f"Ошибка при обработке даты для заказа {order_id}: {e}"
#                     )
#                     continue

#                 # Получаем все товары для этого заказа с учетом поля discount
#                 products_query = """
#                 SELECT productId, text, amount, price, discount, percentDiscount
#                 FROM products
#                 WHERE order_id = ?
#                 """

#                 cursor = await db.execute(products_query, (order_id,))
#                 products = await cursor.fetchall()

#                 for product in products:
#                     (
#                         product_id,
#                         product_name,
#                         quantity,
#                         price,
#                         discount,
#                         percent_discount,
#                     ) = product

#                     # Предотвращаем ошибки с неправильными значениями
#                     if not quantity or quantity <= 0:
#                         quantity = 0
#                     if not price or price <= 0:
#                         price = 0
#                     if not discount or discount < 0:
#                         discount = 0
#                     if not percent_discount or percent_discount < 0:
#                         percent_discount = 0

#                     # Рассчитываем цену с учетом скидки
#                     price_with_discount = price - discount
#                     if price_with_discount < 0:
#                         price_with_discount = 0

#                     # Общая сумма с учетом скидки и количества
#                     total_amount = price_with_discount * quantity

#                     # Вставляем запись в аналитическую таблицу с учетом типа продажи
#                     try:
#                         await db.execute(
#                             """
#                         INSERT OR IGNORE INTO sales_analytics
#                         (order_id, product_id, product_name, quantity, price, discount,
#                          percent_discount, price_with_discount, total_amount,
#                          sale_date, day, month, quarter, year, month_year, tip_prodazu)
#                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                         """,
#                             (
#                                 order_id,
#                                 product_id,
#                                 product_name,
#                                 quantity,
#                                 price,
#                                 discount,
#                                 percent_discount,
#                                 price_with_discount,
#                                 total_amount,
#                                 sale_date,
#                                 day,
#                                 month,
#                                 quarter,
#                                 year,
#                                 month_year,
#                                 tip_prodazu_value,
#                             ),
#                         )

#                         # Проверяем, была ли вставка успешной
#                         changes = db.total_changes
#                         if changes > 0:
#                             processed_count += 1
#                         else:
#                             skipped_count += 1
#                     except Exception as e:
#                         logger.debug(f"Ошибка при вставке записи: {e}")
#                         skipped_count += 1

#             await db.commit()
#             logger.info(
#                 f"Обновлена аналитическая таблица: добавлено {processed_count} записей, пропущено {skipped_count}"
#             )


#     except Exception as e:
#         logger.error(f"Ошибка при обновлении аналитической таблицы: {e}")
async def update_analytics_table():
    """Создает и обновляет улучшенную аналитическую таблицу продаж с учетом скидок, типа продажи и категории товара"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Проверяем существование таблицы
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sales_analytics'"
            )
            table_exists = await cursor.fetchone()

            if table_exists:
                # Проверяем наличие колонки product_category
                cursor = await db.execute("PRAGMA table_info(sales_analytics)")
                columns = await cursor.fetchall()
                has_category_column = any(
                    col[1] == "product_category" for col in columns
                )

                if not has_category_column:
                    # Добавляем колонку для категории товара
                    logger.info(
                        "Добавляем колонку product_category в таблицу sales_analytics"
                    )
                    await db.execute(
                        "ALTER TABLE sales_analytics ADD COLUMN product_category TEXT"
                    )
                    await db.commit()
            else:
                # Создаем таблицу с новой колонкой для категории
                await db.execute(
                    """
                CREATE TABLE sales_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    product_id INTEGER,
                    product_name TEXT,
                    product_category TEXT,       -- Категория товара
                    quantity INTEGER,
                    price REAL,                  -- Исходная цена (без скидки)
                    discount REAL,               -- Скидка на единицу товара
                    percent_discount REAL,       -- Процент скидки
                    price_with_discount REAL,    -- Цена с учетом скидки
                    total_amount REAL,           -- Общая сумма (цена с учетом скидки * количество)
                    sale_date TEXT,              -- YYYY-MM-DD
                    day INTEGER,                 -- День месяца (1-31)
                    month INTEGER,               -- Месяц (1-12)
                    quarter INTEGER,             -- Квартал (1-4)
                    year INTEGER,                -- Год
                    month_year TEXT,             -- MM.YYYY
                    tip_prodazu TEXT,            -- Тип продажи
                    UNIQUE(order_id, product_id)
                )
                """
                )
                await db.commit()
                logger.info(
                    "Создана новая таблица sales_analytics с колонкой категории товара"
                )

            # Получаем заказы, которые еще не обработаны
            query = """
            SELECT o.id, o.orderTime
            FROM orders o
            WHERE EXISTS (
                SELECT 1 FROM products p WHERE p.order_id = o.id
            )
            AND NOT EXISTS (
                SELECT 1 FROM sales_analytics s WHERE s.order_id = o.id
            )
            """

            cursor = await db.execute(query)
            orders = await cursor.fetchall()

            processed_count = 0
            skipped_count = 0

            # Получаем словарь соответствий товар -> категория из таблицы product_category_relations
            category_mapping = {}
            try:
                # Получаем связи товаров с категориями
                category_query = """
                SELECT pcr.product_id, pc.category_name 
                FROM product_category_relations pcr
                JOIN product_categories pc ON pcr.category_id = pc.id
                """
                cursor = await db.execute(category_query)
                relations = await cursor.fetchall()

                # Создаем словарь product_id -> category_name
                for relation in relations:
                    product_id, category_name = relation
                    category_mapping[product_id] = category_name

                logger.info(
                    f"Загружено {len(category_mapping)} связей товаров с категориями"
                )
            except Exception as e:
                logger.error(f"Ошибка при получении связей товаров с категориями: {e}")
                # Продолжаем выполнение даже в случае ошибки

            for order in orders:
                order_id, order_time = order

                # Если нет orderTime, пропускаем
                if not order_time:
                    continue

                # Получаем тип продажи для этого заказа
                tip_prodazu_query = """
                SELECT value
                FROM tip_prodazu
                WHERE order_id = ?
                LIMIT 1
                """

                cursor_tip = await db.execute(tip_prodazu_query, (order_id,))
                tip_row = await cursor_tip.fetchone()
                tip_prodazu_value = tip_row[0] if tip_row else None

                try:
                    # Парсим и форматируем дату
                    dt = datetime.strptime(order_time, "%Y-%m-%d %H:%M:%S")
                    sale_date = dt.strftime("%Y-%m-%d")
                    day = dt.day
                    month = dt.month
                    year = dt.year

                    # Вычисляем квартал (1-4)
                    quarter = (month - 1) // 3 + 1

                    # Формат месяц.год
                    month_year = dt.strftime("%m.%Y")
                except Exception as e:
                    logger.error(
                        f"Ошибка при обработке даты для заказа {order_id}: {e}"
                    )
                    continue

                # Получаем все товары для этого заказа с учетом поля discount
                products_query = """
                SELECT productId, text, amount, price, discount, percentDiscount
                FROM products
                WHERE order_id = ?
                """

                cursor = await db.execute(products_query, (order_id,))
                products = await cursor.fetchall()

                for product in products:
                    (
                        product_id,
                        product_name,
                        quantity,
                        price,
                        discount,
                        percent_discount,
                    ) = product

                    # Получаем категорию товара
                    product_category = category_mapping.get(
                        product_id, "Неизвестная категория"
                    )

                    # Предотвращаем ошибки с неправильными значениями
                    if not quantity or quantity <= 0:
                        quantity = 0
                    if not price or price <= 0:
                        price = 0
                    if not discount or discount < 0:
                        discount = 0
                    if not percent_discount or percent_discount < 0:
                        percent_discount = 0

                    # Рассчитываем цену с учетом скидки
                    price_with_discount = price - discount
                    if price_with_discount < 0:
                        price_with_discount = 0

                    # Общая сумма с учетом скидки и количества
                    total_amount = price_with_discount * quantity

                    # Вставляем запись в аналитическую таблицу с учетом типа продажи и категории
                    try:
                        await db.execute(
                            """
                        INSERT OR IGNORE INTO sales_analytics
                        (order_id, product_id, product_name, product_category, quantity, price, discount, 
                         percent_discount, price_with_discount, total_amount, 
                         sale_date, day, month, quarter, year, month_year, tip_prodazu)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                order_id,
                                product_id,
                                product_name,
                                product_category,
                                quantity,
                                price,
                                discount,
                                percent_discount,
                                price_with_discount,
                                total_amount,
                                sale_date,
                                day,
                                month,
                                quarter,
                                year,
                                month_year,
                                tip_prodazu_value,
                            ),
                        )

                        # Проверяем, была ли вставка успешной
                        changes = db.total_changes
                        if changes > 0:
                            processed_count += 1
                        else:
                            skipped_count += 1
                    except Exception as e:
                        logger.debug(f"Ошибка при вставке записи: {e}")
                        skipped_count += 1

            # Обновляем категории товаров для существующих записей
            if category_mapping:
                try:
                    updated_records = 0
                    for product_id, category_name in category_mapping.items():
                        update_query = """
                        UPDATE sales_analytics 
                        SET product_category = ? 
                        WHERE product_id = ? AND (product_category IS NULL OR product_category = 'Неизвестная категория')
                        """
                        await db.execute(update_query, (category_name, product_id))
                        updated_records += db.total_changes

                    logger.info(
                        f"Обновлены категории для {updated_records} существующих записей"
                    )
                except Exception as e:
                    logger.error(
                        f"Ошибка при обновлении категорий в существующих записях: {e}"
                    )

            await db.commit()
            logger.info(
                f"Обновлена аналитическая таблица: добавлено {processed_count} записей, пропущено {skipped_count}"
            )

    except Exception as e:
        logger.error(f"Ошибка при обновлении аналитической таблицы: {e}")
        import traceback

        logger.error(traceback.format_exc())


async def get_sales_summary_by_month_product():
    """Получает сводку продаж по месяцам и товарам"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row

            # Суммарные продажи по месяцам и товарам
            query = """
            SELECT 
                year_month,
                product_name,
                SUM(quantity) as total_quantity,
                SUM(total_amount) as total_sales
            FROM sales_by_day_product
            GROUP BY year_month, product_name
            ORDER BY year_month DESC, total_sales DESC
            """

            cursor = await db.execute(query)
            results = await cursor.fetchall()

            # Преобразуем в список словарей
            summary = []
            for row in results:
                summary.append(dict(row))
            logger.info(summary)
            return summary
    except Exception as e:
        logger.error(f"Ошибка при получении сводки продаж: {e}")
        return []


async def check_table_structure():
    """Проверяет структуру таблицы products и наличие нужных колонок"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем информацию о структуре таблицы products
        cursor = await db.execute("PRAGMA table_info(products)")
        columns = await cursor.fetchall()

        # Выводим все колонки для отладки
        for column in columns:
            logger.info(f"Колонка в таблице products: {column}")

        # Проверяем наличие колонки Included_in_set
        has_included_column = any(
            column[1].lower() == "included_in_set" for column in columns
        )

        if not has_included_column:
            logger.info("Колонка Included_in_set не найдена, добавляем её")
            await db.execute(
                "ALTER TABLE products ADD COLUMN Included_in_set BOOLEAN DEFAULT FALSE"
            )
            await db.commit()

            # Проверяем, что колонка действительно добавлена
            cursor = await db.execute("PRAGMA table_info(products)")
            new_columns = await cursor.fetchall()
            logger.info(f"Обновленная структура таблицы: {len(new_columns)} колонок")
            return True
        else:
            logger.info("Колонка Included_in_set уже существует в таблице")
            return False


async def parse_xml_and_update_db():
    """Обработка XML-выгрузки и заполнение таблиц"""
    if not os.path.exists(XML_PATH):
        logger.error(f"Файл XML-выгрузки не найден: {XML_PATH}")
        return

    try:
        # Парсим XML
        tree = ET.parse(XML_PATH)
        root = tree.getroot()

        # Получаем пространство имен
        ns = ""
        if "}" in root.tag:
            ns = root.tag.split("}")[0] + "}"

        # Находим категории
        categories = []
        for category in root.findall(f".//{ns}categories/{ns}category"):
            category_id = int(category.get("id"))
            category_name = category.text
            categories.append((category_id, category_name))

        logger.info(f"Найдено {len(categories)} категорий в XML-выгрузке")

        # Находим товары и их категории
        offers = []

        # Собираем все данные о товарах за один проход по XML
        for offer in root.findall(f".//{ns}offers/{ns}offer"):
            offer_id = offer.get("id")
            if offer_id.startswith("id_"):
                offer_id = offer_id[3:]  # Удаляем префикс 'id_'

            article = None
            category_id = None
            name = ""
            description = ""

            # Извлекаем все нужные данные из элемента offer
            for child in offer:
                tag = child.tag
                if ns:
                    tag = tag.replace(ns, "")

                if tag == "article":
                    article = child.text
                elif tag == "categoryId":
                    try:
                        category_id = int(child.text)
                    except (ValueError, TypeError):
                        pass
                elif tag == "name":
                    name = child.text or ""
                elif tag == "description":
                    description = child.text or ""

            # Определяем, является ли товар набором
            is_set = "SET" in name.upper() if name else False

            # Добавляем информацию о товаре в общий список
            offers.append((offer_id, article, category_id, name, description, is_set))

        logger.info(f"Найдено {len(offers)} товаров в XML-выгрузке")

        # Записываем данные в БД
        async with aiosqlite.connect(DB_PATH) as db:
            # Сначала проверяем и при необходимости модифицируем структуру таблицы
            await check_table_structure()

            # Записываем категории
            for category_id, category_name in categories:
                await db.execute(
                    "INSERT OR IGNORE INTO product_categories (category_id, category_name) VALUES (?, ?)",
                    (category_id, category_name),
                )

            # Получаем информацию о наборах
            set_offers = [
                (oid, art, cat_id, name, desc)
                for oid, art, cat_id, name, desc, is_set in offers
                if is_set
            ]
            logger.info(f"Найдено {len(set_offers)} наборов товаров")

            # Получаем список всех товаров из БД для поиска соответствий
            cursor = await db.execute("SELECT productId, text, sku FROM products")
            all_products = await cursor.fetchall()
            product_dict = {
                product[2]: (product[0], product[1]) for product in all_products
            }  # sku -> (productId, text)

            # Анализируем описания наборов для определения входящих в них товаров
            included_articles = set()

            for _, set_article, _, set_name, set_description in set_offers:
                logger.info(
                    f"Анализ набора {set_article}: {set_name} - {set_description}"
                )

                # Пропускаем, если нет описания
                if not set_description:
                    continue

                # Поиск упоминаний товаров в наборе
                product_types = [
                    "Шампунь",
                    "Кондиціонер",
                    "Маска",
                    "Термозахист",
                    "Олія",
                    "Косметичка",
                ]
                variants = ["Magnetisme", "Obsession", "Electrique"]

                # Строим матрицу сочетаний типов продуктов и вариантов
                for product_type in product_types:
                    if product_type not in set_description:
                        continue

                    for variant in variants:
                        if variant not in set_description:
                            continue

                        # Проверяем все товары на соответствие
                        for sku, (product_id, product_name) in product_dict.items():
                            if product_type in product_name and variant in product_name:
                                included_articles.add(sku)
                                logger.info(f"Товар в наборе: {sku} - {product_name}")

            # Обновляем флаг Included_in_set для всех товаров
            # Используем безопасный SQL запрос с проверкой существования колонки
            try:
                # Сначала сбрасываем флаг для всех товаров
                await db.execute("UPDATE products SET Included_in_set = 0")

                # Затем устанавливаем флаг для товаров, входящих в наборы
                for sku in included_articles:
                    await db.execute(
                        "UPDATE products SET Included_in_set = 1 WHERE sku = ?", (sku,)
                    )
                    logger.info(
                        f"Установлен флаг Included_in_set=TRUE для товара с sku={sku}"
                    )

                logger.info(
                    f"Обновлены флаги Included_in_set для {len(included_articles)} товаров"
                )
            except Exception as e:
                logger.error(f"Ошибка при обновлении флага Included_in_set: {e}")
                logger.info("Попробуем альтернативное обновление...")

                # Альтернативный вариант (с явным указанием поля)
                for sku in included_articles:
                    try:
                        await db.execute(
                            'UPDATE products SET "Included_in_set" = 1 WHERE sku = ?',
                            (sku,),
                        )
                    except Exception as e2:
                        logger.error(f"Альтернативное обновление тоже не удалось: {e2}")

            # Связываем товары с категориями
            for _, article, category_id, _, _, _ in offers:
                if not article or not category_id:
                    continue

                # Получаем productId по артикулу (sku)
                cursor = await db.execute(
                    "SELECT productId FROM products WHERE sku = ?", (article,)
                )
                product_row = await cursor.fetchone()

                if not product_row:
                    logger.warning(f"Товар с sku={article} не найден в БД")
                    continue

                product_id = product_row[0]

                # Получаем id категории из таблицы product_categories
                cursor = await db.execute(
                    "SELECT id FROM product_categories WHERE category_id = ?",
                    (category_id,),
                )
                category_row = await cursor.fetchone()

                if not category_row:
                    logger.warning(f"Категория с id={category_id} не найдена в БД")
                    continue

                category_db_id = category_row[0]

                # Связываем товар с категорией
                await db.execute(
                    "INSERT OR IGNORE INTO product_category_relations (product_id, category_id) VALUES (?, ?)",
                    (product_id, category_db_id),
                )

            await db.commit()

            # Проверяем результаты
            cursor = await db.execute("SELECT COUNT(*) FROM product_categories")
            cat_count = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT COUNT(*) FROM product_category_relations")
            rel_count = (await cursor.fetchone())[0]
            logger.info(
                f"Всего связей в таблице product_category_relations: {rel_count}"
            )

            # Пробуем получить количество товаров в наборах разными способами
            try:
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM products WHERE Included_in_set = 1"
                )
                included_count = (await cursor.fetchone())[0]
            except Exception as e:
                logger.error(f"Ошибка при подсчете товаров в наборах: {e}")
                included_count = len(included_articles)

            logger.info(
                f"Результаты: {cat_count} категорий, {rel_count} связей, {included_count} товаров в наборах"
            )

    except Exception as e:
        logger.error(f"Ошибка при обработке XML: {e}")
        import traceback

        logger.error(traceback.format_exc())


async def check_structure():
    """Проверяет структуру таблиц и при необходимости корректирует ее"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем структуру таблицы product_category_relations
        logger.info("Проверка структуры таблицы product_category_relations")
        cursor = await db.execute("PRAGMA table_info(product_category_relations)")
        columns = await cursor.fetchall()

        for col in columns:
            logger.info(f"Колонка: {col}")

        # Проверяем внешние ключи
        logger.info("Проверка внешних ключей")
        cursor = await db.execute("PRAGMA foreign_key_list(product_category_relations)")
        fkeys = await cursor.fetchall()

        for fk in fkeys:
            logger.info(f"Внешний ключ: {fk}")

        # Проверяем структуру таблицы products
        logger.info("Проверка первых 5 записей из таблицы products")
        cursor = await db.execute(
            "SELECT id, productId, sku, text FROM products LIMIT 5"
        )
        products = await cursor.fetchall()

        for prod in products:
            logger.info(f"Товар: {prod}")


async def recreate_tables():
    """Пересоздает таблицы для устранения проблем с внешними ключами"""
    try:
        logger.info("Начинаем пересоздание таблицы product_category_relations")

        async with aiosqlite.connect(DB_PATH) as db:
            # Проверяем существование базы данных
            logger.info(f"Подключились к базе данных: {DB_PATH}")

            # Проверяем наличие таблицы до удаления
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='product_category_relations'"
            )
            table_exists = await cursor.fetchone()
            if table_exists:
                logger.info(
                    "Таблица product_category_relations существует, будет удалена"
                )
            else:
                logger.info("Таблица product_category_relations не существует")

            # Отключаем внешние ключи
            await db.execute("PRAGMA foreign_keys = OFF")
            logger.info("Внешние ключи отключены")

            # Удаляем таблицу если она существует
            await db.execute("DROP TABLE IF EXISTS product_category_relations")
            logger.info("DROP TABLE выполнен")

            # Создаем таблицу заново с правильными внешними ключами
            create_table_sql = """
            CREATE TABLE product_category_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (category_id) REFERENCES product_categories (id),
                UNIQUE(product_id, category_id)
            )
            """
            logger.info(f"Выполняем SQL: {create_table_sql}")
            await db.execute(create_table_sql)
            logger.info("CREATE TABLE выполнен")

            # Фиксируем изменения
            await db.commit()
            logger.info("Изменения зафиксированы (COMMIT)")

            # Проверяем, что таблица создана
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='product_category_relations'"
            )
            table_created = await cursor.fetchone()
            if table_created:
                logger.info("Таблица product_category_relations успешно создана")
            else:
                logger.error(
                    "ОШИБКА: Таблица product_category_relations НЕ была создана!"
                )

            # Проверяем структуру созданной таблицы
            cursor = await db.execute("PRAGMA table_info(product_category_relations)")
            columns = await cursor.fetchall()
            logger.info(f"Колонки созданной таблицы: {columns}")

            # Проверяем внешние ключи
            cursor = await db.execute(
                "PRAGMA foreign_key_list(product_category_relations)"
            )
            fkeys = await cursor.fetchall()
            logger.info(f"Внешние ключи созданной таблицы: {fkeys}")

            # Включаем внешние ключи
            await db.execute("PRAGMA foreign_keys = ON")
            logger.info("Внешние ключи включены")

            logger.info(
                "Пересоздание таблицы product_category_relations завершено успешно"
            )
            return True

    except Exception as e:
        logger.error(f"Ошибка при пересоздании таблицы: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


async def import_relations():
    """Импортирует связи между товарами и категориями напрямую из XML в базу данных"""

    if not os.path.exists(XML_PATH):
        print(f"Ошибка: XML-файл не найден: {XML_PATH}")
        return False

    if not os.path.exists(DB_PATH):
        print(f"Ошибка: База данных не найдена: {DB_PATH}")
        return False

    try:
        # Парсим XML
        tree = ET.parse(XML_PATH)
        root = tree.getroot()

        # Получаем пространство имен (если есть)
        ns = ""
        if "}" in root.tag:
            ns = root.tag.split("}")[0] + "}"

        # Извлекаем данные о товарах и категориях
        products_data = []

        for offer in root.findall(f".//{ns}offers/{ns}offer"):
            article = next((item.text for item in offer.findall(f"{ns}article")), None)
            category_id = next(
                (item.text for item in offer.findall(f"{ns}categoryId")), None
            )

            if article and category_id:
                try:
                    category_id = int(category_id)
                    products_data.append((article, category_id))
                except (ValueError, TypeError):
                    print(
                        f"Предупреждение: Некорректный categoryId для товара {article}"
                    )

        # Подключаемся к базе данных
        async with aiosqlite.connect(DB_PATH) as db:
            # Отключаем внешние ключи
            await db.execute("PRAGMA foreign_keys = OFF")

            # Очищаем таблицу связей
            await db.execute("DELETE FROM product_category_relations")
            print("Таблица product_category_relations очищена")

            # Проверяем наличие данных в таблицах
            cursor = await db.execute("SELECT COUNT(*) FROM products")
            products_count = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT COUNT(*) FROM product_categories")
            categories_count = (await cursor.fetchone())[0]

            print(
                f"В базе данных: {products_count} товаров и {categories_count} категорий"
            )

            # Импортируем связи
            relations_created = 0
            failed_relations = 0

            for article, category_id in products_data:
                # Получаем ID товара
                cursor = await db.execute(
                    "SELECT id FROM products WHERE sku = ?", (article,)
                )
                product_row = await cursor.fetchone()

                if not product_row:
                    print(f"Товар с артикулом {article} не найден в базе данных")
                    failed_relations += 1
                    continue

                product_id = product_row[0]

                # Получаем ID категории
                cursor = await db.execute(
                    "SELECT id FROM product_categories WHERE category_id = ?",
                    (category_id,),
                )
                category_row = await cursor.fetchone()

                if not category_row:
                    print(f"Категория с ID {category_id} не найдена в базе данных")
                    failed_relations += 1
                    continue

                category_db_id = category_row[0]

                # Создаем связь
                try:
                    await db.execute(
                        "INSERT INTO product_category_relations (product_id, category_id) VALUES (?, ?)",
                        (product_id, category_db_id),
                    )
                    relations_created += 1
                except aiosqlite.Error as e:
                    print(
                        f"Ошибка при создании связи для товара {article} и категории {category_id}: {e}"
                    )
                    failed_relations += 1

            # Сохраняем изменения
            await db.commit()

            # Проверяем результат
            cursor = await db.execute("SELECT COUNT(*) FROM product_category_relations")
            relations_count = (await cursor.fetchone())[0]

            print(f"\nРезультаты импорта:")
            print(f"- Создано связей: {relations_created}")
            print(f"- Не удалось создать связей: {failed_relations}")
            print(f"- Всего связей в базе данных: {relations_count}")

            # Выводим примеры связей
            cursor = await db.execute(
                """
                SELECT 
                    p.id, p.sku, p.text, 
                    pc.id, pc.category_id, pc.category_name
                FROM 
                    product_category_relations pcr
                JOIN 
                    products p ON pcr.product_id = p.id
                JOIN 
                    product_categories pc ON pcr.category_id = pc.id
                LIMIT 5
            """
            )

            examples = await cursor.fetchall()

            if examples:
                print("\nПримеры созданных связей:")
                for ex in examples:
                    print(f"Товар: {ex[1]} ({ex[2]}) -> Категория: {ex[4]} ({ex[5]})")

            # Включаем внешние ключи
            await db.execute("PRAGMA foreign_keys = ON")

        return True

    except Exception as e:
        print(f"Ошибка при импорте связей: {e}")
        import traceback

        print(traceback.format_exc())
        return False


async def main():
    if await import_relations():
        print("\nИмпорт связей успешно завершен.")
    else:
        print("\nИмпорт связей не удался из-за ошибок.")


# async def check_table_structure():
#     """Проверяет структуру таблицы products и наличие нужных колонок"""
#     async with aiosqlite.connect(DB_PATH) as db:
#         # Получаем информацию о структуре таблицы products
#         cursor = await db.execute("PRAGMA table_info(products)")
#         columns = await cursor.fetchall()

#         # Выводим все колонки для отладки
#         for column in columns:
#             logger.info(f"Колонка в таблице products: {column}")

#         # Проверяем наличие колонки included_in_set (в нижнем регистре)
#         column_names = [column[1].lower() for column in columns]
#         has_included_column = "included_in_set" in column_names

#         if not has_included_column:
#             logger.info("Колонка included_in_set не найдена, добавляем её")
#             await db.execute(
#                 "ALTER TABLE products ADD COLUMN included_in_set BOOLEAN DEFAULT FALSE"
#             )
#             await db.commit()
#             return True
#         else:
#             logger.info("Колонка included_in_set уже существует в таблице")
#             return False


# async def import_products_from_xml():
#     """Импортирует товары из XML-выгрузки в таблицу products"""
#     if not os.path.exists(XML_PATH):
#         logger.error(f"Файл XML-выгрузки не найден: {XML_PATH}")
#         return False

#     try:
#         # Парсим XML
#         tree = ET.parse(XML_PATH)
#         root = tree.getroot()

#         # Получаем пространство имен
#         ns = ""
#         if "}" in root.tag:
#             ns = root.tag.split("}")[0] + "}"

#         # Находим товары
#         products_imported = 0

#         async with aiosqlite.connect(DB_PATH) as db:
#             # Собираем все данные о товарах за один проход по XML
#             for offer in root.findall(f".//{ns}offers/{ns}offer"):
#                 offer_id = offer.get("id")
#                 if offer_id.startswith("id_"):
#                     offer_id = offer_id[3:]  # Удаляем префикс 'id_'

#                 # Извлекаем все нужные данные из элемента offer
#                 productId = int(offer_id) if offer_id.isdigit() else None
#                 name = None
#                 article = None
#                 barcode = None
#                 price = None
#                 category_id = None
#                 description = None

#                 for child in offer:
#                     tag = child.tag
#                     if ns:
#                         tag = tag.replace(ns, "")

#                     if tag == "name":
#                         name = child.text
#                     elif tag == "article":
#                         article = child.text
#                     elif tag == "barcode":
#                         barcode = child.text
#                     elif tag == "price":
#                         try:
#                             price = float(child.text)
#                         except (ValueError, TypeError):
#                             price = 0
#                     elif tag == "categoryId":
#                         try:
#                             category_id = int(child.text)
#                         except (ValueError, TypeError):
#                             pass
#                     elif tag == "description":
#                         description = child.text

#                 # Проверяем наличие товара в БД
#                 cursor = await db.execute(
#                     "SELECT id FROM products WHERE sku = ?", (article,)
#                 )
#                 existing_product = await cursor.fetchone()

#                 if existing_product:
#                     # Товар уже существует, обновляем его
#                     await db.execute(
#                         """
#                         UPDATE products
#                         SET text = ?, barcode = ?, price = ?, description = ?
#                         WHERE sku = ?
#                     """,
#                         (name, barcode, price, description, article),
#                     )
#                     logger.info(f"Обновлен товар: {article} - {name}")
#                 else:
#                     # Товар не существует, добавляем его
#                     await db.execute(
#                         """
#                         INSERT INTO products
#                         (productId, text, sku, barcode, price, description)
#                         VALUES (?, ?, ?, ?, ?, ?)
#                     """,
#                         (productId, name, article, barcode, price, description),
#                     )
#                     products_imported += 1
#                     logger.info(f"Добавлен новый товар: {article} - {name}")

#             await db.commit()
#             logger.info(f"Импортировано {products_imported} новых товаров из XML")
#             return True

#     except Exception as e:
#         logger.error(f"Ошибка при импорте товаров из XML: {e}")
#         import traceback

#         logger.error(traceback.format_exc())
#         return False


# async def parse_xml_and_update_db():
#     """Обработка XML-выгрузки и заполнение таблиц"""
#     if not os.path.exists(XML_PATH):
#         logger.error(f"Файл XML-выгрузки не найден: {XML_PATH}")
#         return

#     try:
#         # Парсим XML
#         tree = ET.parse(XML_PATH)
#         root = tree.getroot()

#         # Получаем пространство имен
#         ns = ""
#         if "}" in root.tag:
#             ns = root.tag.split("}")[0] + "}"

#         # Находим категории
#         categories = []
#         for category in root.findall(f".//{ns}categories/{ns}category"):
#             category_id = int(category.get("id"))
#             category_name = category.text
#             categories.append((category_id, category_name))

#         logger.info(f"Найдено {len(categories)} категорий в XML-выгрузке")

#         # Находим товары и их категории
#         offers = []

#         # Собираем все данные о товарах за один проход по XML
#         for offer in root.findall(f".//{ns}offers/{ns}offer"):
#             offer_id = offer.get("id")
#             if offer_id.startswith("id_"):
#                 offer_id = offer_id[3:]  # Удаляем префикс 'id_'

#             article = None
#             category_id = None
#             name = ""
#             description = ""

#             # Извлекаем все нужные данные из элемента offer
#             for child in offer:
#                 tag = child.tag
#                 if ns:
#                     tag = tag.replace(ns, "")

#                 if tag == "article":
#                     article = child.text
#                 elif tag == "categoryId":
#                     try:
#                         category_id = int(child.text)
#                     except (ValueError, TypeError):
#                         pass
#                 elif tag == "name":
#                     name = child.text or ""
#                 elif tag == "description":
#                     description = child.text or ""

#             # Определяем, является ли товар набором
#             is_set = "SET" in name.upper() if name else False

#             # Добавляем информацию о товаре в общий список
#             offers.append((offer_id, article, category_id, name, description, is_set))

#         logger.info(f"Найдено {len(offers)} товаров в XML-выгрузке")

#         # Записываем данные в БД
#         async with aiosqlite.connect(DB_PATH) as db:
#             # Сначала проверяем и при необходимости модифицируем структуру таблицы
#             await check_table_structure()

#             # Сначала импортируем товары, чтобы избежать ошибок с отсутствующими товарами
#             await import_products_from_xml()

#             # Записываем категории
#             for category_id, category_name in categories:
#                 await db.execute(
#                     "INSERT OR IGNORE INTO product_categories (category_id, category_name) VALUES (?, ?)",
#                     (category_id, category_name),
#                 )

#             # Получаем информацию о наборах
#             set_offers = [
#                 (oid, art, cat_id, name, desc)
#                 for oid, art, cat_id, name, desc, is_set in offers
#                 if is_set
#             ]
#             logger.info(f"Найдено {len(set_offers)} наборов товаров")

#             # Получаем список всех товаров из БД для поиска соответствий
#             cursor = await db.execute("SELECT productId, text, sku FROM products")
#             all_products = await cursor.fetchall()
#             product_dict = {
#                 product[2]: (product[0], product[1]) for product in all_products
#             }  # sku -> (productId, text)

#             # Анализируем описания наборов для определения входящих в них товаров
#             included_articles = set()

#             for _, set_article, _, set_name, set_description in set_offers:
#                 logger.info(
#                     f"Анализ набора {set_article}: {set_name} - {set_description}"
#                 )

#                 # Пропускаем, если нет описания
#                 if not set_description:
#                     continue

#                 # Поиск упоминаний товаров в наборе
#                 product_types = [
#                     "Шампунь",
#                     "Кондиціонер",
#                     "Маска",
#                     "Термозахист",
#                     "Олія",
#                     "Косметичка",
#                 ]
#                 variants = ["Magnetisme", "Obsession", "Electrique"]

#                 # Строим матрицу сочетаний типов продуктов и вариантов
#                 for product_type in product_types:
#                     if product_type not in set_description:
#                         continue

#                     for variant in variants:
#                         if variant not in set_description:
#                             continue

#                         # Проверяем все товары на соответствие
#                         for sku, (product_id, product_name) in product_dict.items():
#                             if product_type in product_name and variant in product_name:
#                                 included_articles.add(sku)
#                                 logger.info(f"Товар в наборе: {sku} - {product_name}")

#             # Обновляем флаг included_in_set (нижний регистр!) для всех товаров
#             try:
#                 # Сначала сбрасываем флаг для всех товаров
#                 await db.execute("UPDATE products SET included_in_set = 0")

#                 # Затем устанавливаем флаг для товаров, входящих в наборы
#                 for sku in included_articles:
#                     await db.execute(
#                         "UPDATE products SET included_in_set = 1 WHERE sku = ?", (sku,)
#                     )
#                     logger.info(
#                         f"Установлен флаг included_in_set=TRUE для товара с sku={sku}"
#                     )

#                 logger.info(
#                     f"Обновлены флаги included_in_set для {len(included_articles)} товаров"
#                 )
#             except Exception as e:
#                 logger.error(f"Ошибка при обновлении флага included_in_set: {e}")
#                 logger.info("Попробуем альтернативное обновление...")

#                 # Альтернативный вариант (с кавычками вокруг имени поля)
#                 for sku in included_articles:
#                     try:
#                         await db.execute(
#                             'UPDATE products SET "included_in_set" = 1 WHERE sku = ?',
#                             (sku,),
#                         )
#                     except Exception as e2:
#                         logger.error(f"Альтернативное обновление тоже не удалось: {e2}")

#             # Связываем товары с категориями
#             for _, article, category_id, _, _, _ in offers:
#                 if not article or not category_id:
#                     continue

#                 # Получаем productId по артикулу (sku)
#                 cursor = await db.execute(
#                     "SELECT id FROM products WHERE sku = ?", (article,)
#                 )
#                 product_row = await cursor.fetchone()

#                 if not product_row:
#                     logger.warning(f"Товар с sku={article} не найден в БД")
#                     continue

#                 product_id = product_row[0]

#                 # Получаем id категории из таблицы product_categories
#                 cursor = await db.execute(
#                     "SELECT id FROM product_categories WHERE category_id = ?",
#                     (category_id,),
#                 )
#                 category_row = await cursor.fetchone()

#                 if not category_row:
#                     logger.warning(f"Категория с id={category_id} не найдена в БД")
#                     continue

#                 category_db_id = category_row[0]

#                 # Связываем товар с категорией
#                 await db.execute(
#                     "INSERT OR IGNORE INTO product_category_relations (product_id, category_id) VALUES (?, ?)",
#                     (product_id, category_db_id),
#                 )

#             await db.commit()

#             # Проверяем результаты
#             cursor = await db.execute("SELECT COUNT(*) FROM product_categories")
#             cat_count = (await cursor.fetchone())[0]

#             cursor = await db.execute("SELECT COUNT(*) FROM product_category_relations")
#             rel_count = (await cursor.fetchone())[0]

#             # Пробуем получить количество товаров в наборах
#             try:
#                 cursor = await db.execute(
#                     "SELECT COUNT(*) FROM products WHERE included_in_set = 1"
#                 )
#                 included_count = (await cursor.fetchone())[0]
#             except Exception as e:
#                 logger.error(f"Ошибка при подсчете товаров в наборах: {e}")
#                 included_count = len(included_articles)

#             logger.info(
#                 f"Результаты: {cat_count} категорий, {rel_count} связей, {included_count} товаров в наборах"
#             )

#     except Exception as e:
#         logger.error(f"Ошибка при обработке XML: {e}")
#         import traceback

#         logger.error(traceback.format_exc())


async def main():
    
    
    # await get_sales_summary_by_month_product()

    # """Основная функция для запуска процесса"""
    # # Создаем базу данных, если она не существует

    ## Создание БД
    # await create_database()
    
    # # Парсинг категорий
    # await parse_xml_and_update_db()


    # # await update_order_time_look_for_existing_orders()
    # # Обработка данных из JSON строки или файла
    # # Можно раскомментировать нужный вариант
    # # await process_json_file('путь_к_файлу.json')
    # # Читаем содержимое файла

    # # Загрузка старых данных
    # recordings_output_file = data_directory / f"recording_014.json"
    # await process_order(recordings_output_file)
    
    
    ## Аналитеческая таблица
    # await update_analytics_table()
    
    # # # Выгрузка в  Google Sheets
    # await export_orders_to_sheets()


if __name__ == "__main__":
    # Для загрузки старых данных
    # get_salesdrive_orders_old_data()

    # get_salesdrive_orders()
    asyncio.run(main())
