import asyncio
import json
import os.path
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import aiosqlite
import gspread
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from loguru import logger
from oauth2client.service_account import ServiceAccountCredentials

SALESDRIVE_API = "dyzcupX2GKd8zUCrHPUlUIGbB2LuAQ-p_tREmYcCJ8juFvarMV8m40wgVzW4BununZtQq0XPzH5E3Wc6-pHQ6Ph05rgilWJvL0zW"
# Путь к файлу базы данных
DB_PATH = "orders_database.db"

# Путь к вашему JSON файлу с ключами сервисного аккаунта Google
GOOGLE_CREDENTIALS_PATH = "credentials.json"
# ID Google таблицы, в которую будем выгружать данные
SPREADSHEET_ID = "1C_f68yiRyBuDD3ObaSxmDZSZWmsK28ln7MOP8TcUPVA"
# Название листа в таблице
SHEET_NAME = "Orders"

# Путь к папкам и файлу для данных
current_directory = Path.cwd()
data_directory = current_directory / "data"
log_directory = current_directory / "log"
configuration_directory = current_directory / "configuration"
call_recording_directory = current_directory / "call_recording"
data_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)

call_recording_directory.mkdir(parents=True, exist_ok=True)
temp_data_output_file = data_directory / "temp_data.json"
recordings_output_file = data_directory / "recording.json"
result_output_file = data_directory / "result.json"
invalid_json = data_directory / "invalid.json"
PROCESSED_FILES_CACHE = data_directory / "processed_files.json"
service_account_file = configuration_directory / "service_account.json"
log_file_path = log_directory / "log_message.log"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def get_salesdrive_orders(date_from=None, date_to=None):
    try:
        # Если даты не указаны, используем последние 24 часа
        if not date_from or not date_to:
            date_to = datetime.now()
            date_from = date_to - timedelta(days=1)
            date_to = date_to.replace(hour=23, minute=59, second=59)
            date_from = date_from.replace(hour=0, minute=0, second=0)
        # date_from = datetime(2024, 7, 1, 0, 0, 0)  # 01.07.2024 00:00:00
        # Форматируем даты
        date_from_str = date_from.strftime("%Y-%m-%d %H:%M:%S")
        date_to_str = date_to.strftime("%Y-%m-%d %H:%M:%S")

        url = "https://leia.salesdrive.me/api/order/list/"
        headers = {"Form-Api-Key": SALESDRIVE_API}
        # page = 14
        params = {
            "filter[orderTime][from]": date_from_str,
            "filter[orderTime][to]": date_to_str,
            "page": 1,
            "limit": 100,
        }

        #    logger.info(f"Отправляем запрос на URL: {url} с параметрами: {params}")

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=(10, 30),  # (connect timeout, read timeout)
        )

        #    logger.info(f"Получен ответ со статусом: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            write_recordings_to_json(recordings_output_file, data)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_order(recordings_output_file))
            loop.close()
        else:
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
            shipping_method INTEGER,
            payment_method INTEGER,
            shipping_address TEXT,
            comment TEXT,
            timeEntryOrder TEXT,
            holderTime TEXT,
            document_ord_check TEXT,
            discountAmount REAL,
            orderTime TEXT,
            updateAt TEXT,
            statusId INTEGER,
            paymentDate TEXT,
            rejectionReason TEXT,
            userId INTEGER,
            paymentAmount REAL,
            commissionAmount REAL,
            costPriceAmount REAL,
            shipping_costs REAL,
            expensesAmount REAL,
            profitAmount REAL,
            typeId INTEGER,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            value INTEGER,
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

        await db.commit()
        logger.info("База данных создана успешно")


async def insert_order_data(order_data):
    """Вставка всех данных заказа в созданные таблицы"""
    order_id = None
    try:
        order_id = order_data.get("id")
        if not order_id:
            logger.info("Ошибка: отсутствует ID заказа в данных")
            return False

        async with aiosqlite.connect(DB_PATH) as db:
            # Проверяем, существует ли уже запись с таким ID
            cursor = await db.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
            existing_record = await cursor.fetchone()

            if existing_record:
                logger.warning(f"Заказ с ID {order_id} уже существует в базе данных")
                return False

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
                utmCampaign, utmContent, utmTerm, uploaded_to_sheets
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, FALSE
            )
            """,
                (
                    order_data.get("id"),
                    order_data.get("formId"),
                    order_data.get("version"),
                    order_data.get("organizationId"),
                    order_data.get("shipping_method"),
                    order_data.get("payment_method"),
                    order_data.get("shipping_address"),
                    order_data.get("comment"),
                    order_data.get("timeEntryOrder"),
                    order_data.get("holderTime"),
                    order_data.get("document_ord_check"),
                    order_data.get("discountAmount"),
                    order_data.get("orderTime"),
                    order_data.get("updateAt"),
                    order_data.get("statusId"),
                    order_data.get("paymentDate"),
                    order_data.get("rejectionReason"),
                    order_data.get("userId"),
                    order_data.get("paymentAmount"),
                    order_data.get("commissionAmount"),
                    order_data.get("costPriceAmount"),
                    order_data.get("shipping_costs"),
                    order_data.get("expensesAmount"),
                    order_data.get("profitAmount"),
                    order_data.get("typeId"),
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

            # Вставляем tipProdazu1
            tip_list = order_data.get("tipProdazu1", [])
            if tip_list is not None:  # Проверка на None
                for tip in tip_list:
                    await db.execute(
                        "INSERT INTO tip_prodazu (order_id, value) VALUES (?, ?)",
                        (order_id, tip),
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
            logger.info(f"Заказ с ID {order_id} успешно добавлен в базу данных")
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


def upload_to_google_sheets(orders: List[Dict[str, Any]]):
    """Выгрузка данных в Google Sheets"""
    if not orders:
        logger.error("Нет данных для выгрузки в Google Sheets")
        return

    try:
        # Настройка учетных данных
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            GOOGLE_CREDENTIALS_PATH, scope
        )
        client = gspread.authorize(creds)

        # Открытие таблицы
        spreadsheet = client.open_by_id(SPREADSHEET_ID)
        worksheet = None

        # Проверяем, существует ли лист
        try:
            worksheet = spreadsheet.worksheet(SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            # Если лист не существует, создаем его
            worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=1000, cols=20)

        # Подготовка заголовков таблицы
        headers = [
            "ID Заказа",
            "Статус",
            "Дата Заказа",
            "Сумма",
            "Способ Оплаты",
            "Клиент",
            "Телефон",
            "Email",
            "Адрес Доставки",
            "Товары",
        ]

        # Проверяем, есть ли уже заголовки
        existing_headers = worksheet.row_values(1)
        if not existing_headers:
            worksheet.append_row(headers)

        # Подготовка и загрузка данных заказов
        for order in orders:
            order_data = order["data"]

            # Контактная информация
            primary_contact = order_data.get("primaryContact", {})
            name = f"{primary_contact.get('lName', '')} {primary_contact.get('fName', '')}".strip()
            phone = (
                primary_contact.get("phone", [""])[0]
                if primary_contact.get("phone")
                else ""
            )
            email = (
                primary_contact.get("email", [""])[0]
                if primary_contact.get("email")
                else ""
            )

            # Товары
            products = []
            for product in order_data.get("products", []):
                product_text = product.get("text", "")
                amount = product.get("amount", 0)
                price = product.get("price", 0)
                if product_text and amount > 0:
                    products.append(f"{product_text} (кол-во: {amount}, цена: {price})")

            products_text = "; ".join(products)

            # Формирование строки для добавления
            row_data = [
                order_data.get("id", ""),  # ID Заказа
                order_data.get("statusId", ""),  # Статус
                order_data.get("orderTime", ""),  # Дата Заказа
                order_data.get("paymentAmount", 0),  # Сумма
                order_data.get("payment_method", ""),  # Способ Оплаты
                name,  # Клиент
                phone,  # Телефон
                email,  # Email
                order_data.get("shipping_address", ""),  # Адрес Доставки
                products_text,  # Товары
            ]

            # Добавляем данные в таблицу
            worksheet.append_row(row_data)

            # Помечаем заказ как выгруженный
            asyncio.create_task(mark_as_uploaded(order["id"]))

        logger.info(
            f"Данные успешно выгружены в Google Sheets, обработано заказов: {len(orders)}"
        )

    except Exception as e:
        logger.error(f"Ошибка при выгрузке в Google Sheets: {e}")


async def process_json_file(file_path: str):
    """Обработка JSON файла и загрузка данных в БД"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Проверяем, является ли содержимое объектом или массивом
            content = f.read().strip()
            if content.startswith("[") and content.endswith("]"):
                data = json.loads(content)
                for order in data:
                    await insert_order_data(order)
            else:
                # Если это один объект, а не массив
                data = json.loads(content)
                await insert_order_data(data)

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
    except Exception as e:
        logger.error(f"Ошибка обработки файла: {e}")


async def process_order(file_path: str):
    """Обработка JSON файла и загрузка данных в БД"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

            # Очищаем от возможных терминирующих запятых в конце объектов JSON
            if content.endswith(","):
                content = content[:-1]

            # Если содержимое не обёрнуто в массив или объект, обрамляем его в массив
            if not (content.startswith("[") or content.startswith("{")):
                content = f"[{content}]"
            elif content.startswith("{") and content.endswith("}"):
                # Проверяем, возможно это один объект, который нужно обрабатывать как массив с одним элементом
                try:
                    data = json.loads(content)
                    # Если это объект со свойством "data", извлекаем данные
                    if "data" in data and isinstance(data["data"], list):
                        # Обрабатываем каждый заказ в массиве data
                        orders = data["data"]
                        logger.info(f"Найден массив 'data' с {len(orders)} заказами")
                        for order in orders:
                            await insert_order_data(order)
                        return
                    else:
                        # Это один заказ
                        await insert_order_data(data)
                        return
                except json.JSONDecodeError:
                    # Если не удалось декодировать как объект, продолжаем обработку как есть
                    pass

            # Пытаемся проанализировать и выявить структуру JSON
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    # Это массив заказов
                    logger.info(f"Обрабатываем массив из {len(data)} заказов")
                    for order in data:
                        await insert_order_data(order)
                elif isinstance(data, dict):
                    # Проверяем, возможно это словарь с массивом заказов в свойстве "data"
                    if "data" in data and isinstance(data["data"], list):
                        orders = data["data"]
                        logger.info(f"Найден массив 'data' с {len(orders)} заказами")
                        for order in orders:
                            await insert_order_data(order)
                    else:
                        # Это один заказ
                        logger.info("Обрабатываем одиночный заказ")
                        await insert_order_data(data)
                else:
                    logger.error(f"Неподдерживаемый формат данных в файле: {file_path}")
            except json.JSONDecodeError as e:
                # Возможно, файл содержит несколько объектов JSON, разделенных переносами строк
                # (не действительный JSON формат, но часто встречается в логах)
                lines = content.strip().split("\n")
                valid_jsons = []

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Убираем завершающую запятую, если она есть
                    if line.endswith(","):
                        line = line[:-1]

                    try:
                        json_obj = json.loads(line)
                        valid_jsons.append(json_obj)
                    except json.JSONDecodeError:
                        logger.error(
                            f"Пропущена строка с неверным форматом JSON: {line[:50]}..."
                        )

                if valid_jsons:
                    logger.info(
                        f"Обрабатываем {len(valid_jsons)} объектов JSON из отдельных строк"
                    )
                    for order in valid_jsons:
                        await insert_order_data(order)
                else:
                    # Если не удалось обработать ни один объект, сообщаем об ошибке
                    logger.error(
                        f"Не удалось распознать формат данных в файле: {file_path}"
                    )
                    logger.error(f"Ошибка JSON: {e}")

    except Exception as e:
        logger.error(f"Ошибка при обработке файла {file_path}: {e}")


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

                    # Формируем строку с информацией о продукте
                    product_str = f"{p_dict.get('text')} (кол-во: {p_dict.get('amount')}, цена: {p_dict.get('price')})"
                    products_info.append(product_str)

                order_dict["products_info"] = " | ".join(products_info)

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
        ]
        for field in special_fields:
            if field in all_headers:
                headers.append(field)
                all_headers.remove(field)

        # Добавляем оставшиеся поля в алфавитном порядке
        for field in sorted(all_headers):
            headers.append(field)

        # Подключаемся к Google Sheets
        spreadsheet = connect_to_google_sheets()

        # Подготавливаем лист
        worksheet = prepare_sheet(spreadsheet, SHEET_NAME, headers)

        # Выгружаем данные
        upload_data_to_sheet(worksheet, orders_data)

        # Отмечаем заказы как выгруженные
        order_ids = [order["id"] for order in orders_data]
        await mark_orders_as_uploaded(order_ids)

        logger.info("Экспорт данных в Google Sheets завершен")

    except Exception as e:
        logger.error(f"Ошибка при экспорте данных в Google Sheets: {e}")


async def main():
    """Основная функция для запуска процесса"""
    # Создаем базу данных, если она не существует
    await create_database()

    # Обработка данных из JSON строки или файла
    # Можно раскомментировать нужный вариант
    # await process_json_file('путь_к_файлу.json')
    # Читаем содержимое файла
    # Пример JSON строки (можно заменить на фактические данные)
    # recordings_output_file = data_directory / f"recording_14.json"
    # await process_order(recordings_output_file)
    await export_orders_to_sheets()

    # # Получаем заказы, которые еще не выгружены в Google Sheets
    # non_uploaded_orders = await get_non_uploaded_orders()

    # # Выгружаем данные в Google Sheets
    # if non_uploaded_orders:
    #     # Этот вызов будет блокирующим, так как библиотека gspread не поддерживает асинхронность
    #     upload_to_google_sheets(non_uploaded_orders)
    # else:
    #     print("Нет новых заказов для выгрузки в Google Sheets")


if __name__ == "__main__":
    # get_salesdrive_orders()
    asyncio.run(main())
