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

            # Вставляем tipProdazu1 с заменой числовых значений на текст
            tip_list = order_data.get("tipProdazu1", [])
            if tip_list is not None:  # Проверка на None
                # Получаем соответствие ID -> текст из глобальных метаданных
                global metadata
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
