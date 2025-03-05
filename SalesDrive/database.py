import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

import aiosqlite
from loguru import logger

from models import Order, DeliveryData, Contact, Product, SaleAnalytic, Metadata
from utils import parse_order_date, format_order_time_look


class Database:
    """Класс для работы с базой данных SQLite."""
    
    def __init__(self, db_path: str):
        """
        Инициализация класса работы с базой данных.
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.metadata = None  # Метаданные будут загружены позже
    
    def set_metadata(self, metadata: Metadata):
        """Устанавливает метаданные для использования в базе данных."""
        self.metadata = metadata
        
    async def create_database(self) -> None:
        """Создание базы данных и таблиц со всеми полями из JSON."""
        async with aiosqlite.connect(self.db_path) as db:
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
                orderTimeLook TEXT
            )
            """
            )

            # Создаем индексы для оптимизации запросов
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(statusId)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_upload ON orders(uploaded_to_sheets)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(orderTime)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_time_look ON orders(orderTimeLook)")

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

            # Таблица для категорий продуктов
            await db.execute(
                """
            CREATE TABLE IF NOT EXISTS product_categories (
                id INTEGER PRIMARY KEY,
                name TEXT,
                parent_id INTEGER,
                FOREIGN KEY (parent_id) REFERENCES product_categories (id)
            )
            """
            )
            
            # Таблица для связи продуктов и категорий
            await db.execute(
                """
            CREATE TABLE IF NOT EXISTS product_category_mappings (
                product_sku TEXT,
                category_id INTEGER,
                PRIMARY KEY (product_sku, category_id),
                FOREIGN KEY (category_id) REFERENCES product_categories (id)
            )
            """
            )

            # Таблица для аналитики продаж
            await db.execute(
                """
            CREATE TABLE IF NOT EXISTS sales_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                product_name TEXT,
                quantity INTEGER,
                price REAL,
                discount REAL,
                percent_discount REAL,
                price_with_discount REAL,
                total_amount REAL,
                sale_date TEXT,
                day INTEGER,
                month INTEGER,
                quarter INTEGER,
                year INTEGER,
                month_year TEXT,
                UNIQUE(order_id, product_id),
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
            """
            )
            
            # Создаем индексы для таблицы аналитики
            await db.execute("CREATE INDEX IF NOT EXISTS idx_analytics_month_year ON sales_analytics(month_year)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_analytics_product ON sales_analytics(product_id)")
            
            # Витрина данных для анализа продаж по категориям и SKU
            await db.execute("""
            CREATE VIEW IF NOT EXISTS product_analytics AS
            SELECT 
                p.sku, p.text as product_name, 
                COUNT(DISTINCT o.id) as order_count,
                SUM(p.amount) as units_sold,
                SUM(p.price * p.amount) as total_revenue,
                o.orderTimeLook as month_year
            FROM products p
            JOIN orders o ON p.order_id = o.id
            GROUP BY p.sku, o.orderTimeLook
            """)

            await db.commit()
            logger.info("База данных успешно создана или обновлена")

    async def insert_or_update_order_data(self, order_data: Dict[str, Any]) -> bool:
        """
        Вставка или обновление данных заказа в БД в зависимости от статуса.
        
        Args:
            order_data: Словарь с данными заказа
            
        Returns:
            bool: True если заказ был добавлен или обновлен, False в противном случае
        """
        order_id = None

        try:
            order_id = order_data.get("id")
            if not order_id:
                logger.error("Ошибка: отсутствует ID заказа в данных")
                return False

            # Получаем текстовое представление для statusId из JSON
            statusId = order_data.get("statusId")
            statusId_text = str(statusId)

            if statusId is not None and self.metadata and "statusId" in self.metadata.__dict__:
                status_mapping = self.metadata.statusId
                statusId_text = status_mapping.get(statusId, str(statusId))

            # Получаем текстовое представление для typeId
            typeId = order_data.get("typeId")
            typeId_text = str(typeId)
            if typeId is not None and self.metadata and "typeId" in self.metadata.__dict__:
                type_mapping = self.metadata.typeId
                typeId_text = type_mapping.get(typeId, str(typeId))

            # shipping_method ID Переводим в текст
            shipping_method = order_data.get("shipping_method")
            shipping_method_text = str(shipping_method)

            if shipping_method is not None and self.metadata and "shipping_method" in self.metadata.__dict__:
                type_mapping = self.metadata.shipping_method
                shipping_method_text = type_mapping.get(shipping_method, str(shipping_method))

            # payment_method ID Переводим в текст
            payment_method = order_data.get("payment_method")
            payment_method_text = str(payment_method)

            if payment_method is not None and self.metadata and "payment_method" in self.metadata.__dict__:
                type_mapping = self.metadata.payment_method
                payment_method_text = type_mapping.get(payment_method, str(payment_method))

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

            async with aiosqlite.connect(self.db_path) as db:
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
                    if self.metadata and "statusId" in self.metadata.__dict__:
                        status_mapping = self.metadata.statusId
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
                        await self._update_order_data(
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
                    await self._insert_order_data(
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
                logger.debug(f"Подробная информация об ошибке: {traceback.format_exc()}")
            except:
                pass
            return False

    async def _insert_order_data(
        self, 
        db: aiosqlite.Connection,
        order_id: int, 
        order_data: Dict[str, Any],
        typeId_text: str,
        statusId_text: str,
        payment_method_text: str,
        shipping_method_text: str,
    ) -> bool:
        """
        Вставка нового заказа в БД.
        
        Args:
            db: Соединение с базой данных
            order_id: ID заказа
            order_data: Словарь с данными заказа
            typeId_text: Текстовое представление типа заказа
            statusId_text: Текстовое представление статуса заказа
            payment_method_text: Текстовое представление метода оплаты
            shipping_method_text: Текстовое представление метода доставки
            
        Returns:
            bool: True если заказ был добавлен успешно, False в противном случае
        """
        try:
            if not order_id:
                logger.info("Ошибка: отсутствует ID заказа в данных")
                return False
                
            # Форматируем orderTimeLook
            order_time = order_data.get("orderTime")
            order_time_look = format_order_time_look(order_time)

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
                    utmCampaign, utmContent, utmTerm, uploaded_to_sheets, orderTimeLook
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, FALSE, ?
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
                tip_mapping = self.metadata.tipProdazu1 if self.metadata else {}

                for tip in tip_list:
                    # Получаем текстовое представление для числового значения
                    tip_text = tip_mapping.get(
                        tip, str(tip)
                    )  # Если нет в словаре, используем строковое значение

                    await db.execute(
                        "INSERT INTO tip