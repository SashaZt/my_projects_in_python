import json
import sqlite3
import sys
import time
from pathlib import Path

import requests
from logger import logger
from main_token import get_token, load_product_data, save_json_data, validyty_token

current_directory = Path.cwd()
data_directory = current_directory / "data"
config_directory = current_directory / "config"
db_directory = current_directory / "db"
db_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
config_json_file = config_directory / "config.json"
# Пути к файлам с ключами
keys_10_usd_file = data_directory / "Roblox_10_usd.txt"
keys_25_usd_file = data_directory / "Roblox_25_usd.txt"
config = load_product_data(config_json_file)
DB_NAME = db_directory / config["db"]["DB_NAME"]
ROBLOX_PRODUCTS_FILE = data_directory / config["products"]["ROBLOX_PRODUCTS_FILE"]


# Создание базы данных и таблицы
def init_db():
    """
    Создает базу данных с таблицами для заказов, товаров и ключей.
    Загружает список товаров из JSON-файла.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Создаем таблицу для заказов
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        status INTEGER,
        item_name TEXT,
        user_phone TEXT,
        first_name TEXT,
        last_name TEXT,
        second_name TEXT,
        full_name TEXT,
        created TEXT,
        amount TEXT,
        key_id INTEGER DEFAULT NULL,
        key_sent_at TEXT DEFAULT NULL,
        message_sent BOOLEAN DEFAULT 0,
        FOREIGN KEY (key_id) REFERENCES product_keys (id)
    )
    """
    )

    # Создаем таблицу для товаров
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        card_value INTEGER,  -- Номинал карты в $
        card_count INTEGER,  -- Количество карт
        robux_amount INTEGER, -- Количество ROBUX
        active BOOLEAN DEFAULT 0
    )
    """
    )

    # Создаем таблицу для ключей
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS product_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        key_value TEXT UNIQUE,
        is_used BOOLEAN DEFAULT 0,
        order_id INTEGER DEFAULT NULL,
        used_at TEXT DEFAULT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (order_id) REFERENCES orders (id)
    )
    """
    )

    if ROBLOX_PRODUCTS_FILE.exists():
        try:
            with open(ROBLOX_PRODUCTS_FILE, "r", encoding="utf-8") as file:
                products = json.load(file)

                # Счетчики для статистики
                products_added = 0
                keys_added = 0

                # Добавляем товары и их ключи в базу данных
                for product in products:
                    product_name = product["name"]
                    card_value = product.get("card_value", 0)
                    card_count = product.get("card_count", 0)
                    robux_amount = product.get("robux_amount", 0)

                    # Вставляем товар в базу данных
                    cursor.execute(
                        """
                    INSERT OR IGNORE INTO products 
                    (name, card_value, card_count, robux_amount) 
                    VALUES (?, ?, ?, ?)
                    """,
                        (product_name, card_value, card_count, robux_amount),
                    )

                    # Если товар был успешно добавлен или уже существовал
                    if cursor.rowcount > 0:
                        products_added += 1

                    # Получаем ID продукта (существующего или только что добавленного)
                    cursor.execute(
                        "SELECT id FROM products WHERE name = ?", (product_name,)
                    )
                    product_id = cursor.fetchone()[0]

                    # Добавляем ключи для этого продукта
                    product_keys = product.get("product_keys", [])
                    for key_value in product_keys:
                        # Проверяем, существует ли уже такой ключ
                        cursor.execute(
                            "SELECT id FROM product_keys WHERE key_value = ?",
                            (key_value,),
                        )
                        existing_key = cursor.fetchone()

                        if not existing_key:
                            # Добавляем новый ключ
                            cursor.execute(
                                """
                                INSERT INTO product_keys (product_id, key_value, is_used)
                                VALUES (?, ?, ?)
                                """,
                                (product_id, key_value, 0),
                            )
                            keys_added += 1

                conn.commit()
                logger.info(
                    f"Загружено {products_added} товаров и {keys_added} ключей из {ROBLOX_PRODUCTS_FILE}"
                )
        except json.JSONDecodeError:
            logger.error(f"Ошибка чтения файла {ROBLOX_PRODUCTS_FILE}")
    else:
        logger.error(f"Файл {ROBLOX_PRODUCTS_FILE} не найден")

    # Создаем индексы для оптимизации запросов
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_key_id ON orders (key_id)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_product_keys_product_id ON product_keys (product_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_product_keys_is_used ON product_keys (is_used)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_product_keys_order_id ON product_keys (order_id)"
    )

    conn.commit()

    # Выводим статистику
    cursor.execute("SELECT COUNT(*) FROM products")
    products_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM product_keys")
    keys_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders")
    orders_count = cursor.fetchone()[0]

    logger.info(f"База данных {DB_NAME} инициализирована:")
    logger.info(f"- Товаров: {products_count}")
    logger.info(f"- Ключей: {keys_count}")
    logger.info(f"- Заказов: {orders_count}")

    conn.close()


init_db()


# Сохранение заказов в базу данных
def save_parsed_orders_to_db(parsed_orders):
    """
    Сохраняет обработанные заказы из parsed_orders.json в базу данных
    """
    # Путь к файлу с обработанными заказами
    # parsed_orders_file = data_directory / "parsed_orders.json"

    # # Проверяем существование файла
    # if not parsed_orders_file.exists():
    #     logger.error(f"Файл {parsed_orders_file} не найден")
    #     return False

    # # Загружаем обработанные заказы
    # parsed_orders = load_product_data(parsed_orders_file)
    # if not parsed_orders:
    #     logger.error("Не удалось загрузить обработанные заказы")
    #     return False

    # Подключаемся к базе данных
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    orders_updated = 0
    orders_inserted = 0

    for order in parsed_orders:
        # Получаем данные заказа
        order_id = order.get("order_id")
        item_name = order.get("product", "")
        user_phone = order.get("user_phone", "")
        created = order.get("created", "")
        amount = order.get("amount", "")
        full_name = order.get("full_name", "")
        status_payment = order.get("status_payment", "")

        # Определяем статус заказа на основе status_payment
        # Можно настроить соответствие между статусами
        status = 1  # Значение по умолчанию
        if status_payment == "Сума заблокована":
            status = 7  # Предположительно "оплачено"

        # Разбиваем полное имя на компоненты
        name_parts = full_name.split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        second_name = name_parts[2] if len(name_parts) > 2 else ""

        # Проверяем, существует ли уже такой заказ
        cursor.execute("SELECT id, status FROM orders WHERE id = ?", (order_id,))
        existing_order = cursor.fetchone()

        if existing_order:
            # Проверяем, изменился ли статус заказа
            old_status = existing_order[1]
            status_changed = old_status != status

            # Обновляем существующий заказ
            cursor.execute(
                """
            UPDATE orders SET 
                status = ?,
                item_name = ?,
                user_phone = ?,
                first_name = ?,
                last_name = ?,
                second_name = ?,
                full_name = ?,
                created = ?,
                amount = ?
            WHERE id = ?
            """,
                (
                    status,
                    item_name,
                    user_phone,
                    first_name,
                    last_name,
                    second_name,
                    full_name,
                    created,
                    amount,
                    order_id,
                ),
            )

            orders_updated += 1

            # Если статус изменился на "оплачено", можно выполнить дополнительные действия
            if status_changed and status == 5:
                logger.info(f"Статус заказа #{order_id} изменился на 'оплачено'")
                # Здесь можно добавить логику для обработки оплаченных заказов
                # Например, отправку уведомления, выделение ключа и т.д.
        else:
            # Добавляем новый заказ
            cursor.execute(
                """
            INSERT INTO orders (
                id, status, item_name, user_phone, first_name, 
                last_name, second_name, full_name, created, amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    order_id,
                    status,
                    item_name,
                    user_phone,
                    first_name,
                    last_name,
                    second_name,
                    full_name,
                    created,
                    amount,
                ),
            )

            orders_inserted += 1

            # Если новый заказ уже оплачен, можно выполнить дополнительные действия
            if status == 5:
                logger.info(f"Новый оплаченный заказ #{order_id}")
                # Здесь можно добавить логику для обработки новых оплаченных заказов

    conn.commit()

    # Выводим статистику
    logger.info(f"Обработано заказов: {len(parsed_orders)}")
    logger.info(f"Добавлено новых заказов: {orders_inserted}")
    logger.info(f"Обновлено существующих заказов: {orders_updated}")

    conn.close()
    return True


def get_next_available_key_for_orders():
    """
    Проверяет таблицу заказов на наличие заказов без отправленных ключей
    и выделяет для них следующий свободный ключ соответствующего номинала.
    """
    conn = sqlite3.connect(DB_NAME)
    # Включаем поддержку внешних ключей
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        # Получаем заказы, для которых еще не были отправлены ключи
        cursor.execute(
            """
        SELECT o.id, o.item_name, o.status
        FROM orders o
        WHERE o.key_sent_at IS NULL AND o.status = 7  -- статус 7 обычно означает "оплачено"
        """
        )

        orders_without_keys = cursor.fetchall()

        if not orders_without_keys:
            logger.info("Нет заказов, требующих выделения ключей")
            return []

        result = []

        for order_id, item_name, status in orders_without_keys:
            logger.info(f"Обработка заказа #{order_id} - {item_name}")

            # Получаем информацию о продукте по его имени
            cursor.execute(
                """
            SELECT id, card_value, card_count
            FROM products
            WHERE name = ?
            """,
                (item_name,),
            )

            product_info = cursor.fetchone()

            if not product_info:
                logger.error(f"Продукт '{item_name}' не найден в базе данных")
                continue

            product_id, card_value, card_count = product_info

            # Проверяем, какие именно ключи нам нужны (номинал и количество)
            if card_count == 1:
                # Если это одна карта, просто ищем свободный ключ для этого продукта
                cursor.execute(
                    """
                SELECT pk.id, pk.key_value 
                FROM product_keys pk
                WHERE pk.product_id = ? AND pk.is_used = 0
                LIMIT 1
                """,
                    (product_id,),
                )

                key_info = cursor.fetchone()

                if key_info:
                    key_id, key_value = key_info

                    # Отмечаем ключ как использованный и привязываем его к заказу
                    cursor.execute(
                        """
                    UPDATE product_keys
                    SET is_used = 1, order_id = ?, used_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                        (order_id, key_id),
                    )

                    # Обновляем информацию о заказе
                    cursor.execute(
                        """
                    UPDATE orders
                    SET key_id = ?, key_sent_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                        (key_id, order_id),
                    )

                    result.append(
                        {
                            "order_id": order_id,
                            "product": item_name,
                            "key_id": key_id,
                            "key_value": key_value,
                        }
                    )

                    logger.info(f"Для заказа #{order_id} выделен ключ: {key_value}")
                else:
                    logger.error(f"Нет доступных ключей для продукта '{item_name}'")
            else:
                # Если это комбинация карт, ищем ключи для базового номинала
                # Находим продукт с таким же номиналом, но для одной карты
                cursor.execute(
                    """
                SELECT id 
                FROM products
                WHERE card_value = ? AND card_count = 1
                LIMIT 1
                """,
                    (card_value,),
                )

                base_product_info = cursor.fetchone()

                if not base_product_info:
                    logger.error(f"Не найден базовый продукт с номиналом {card_value}$")
                    continue

                base_product_id = base_product_info[0]

                # Ищем нужное количество свободных ключей
                cursor.execute(
                    """
                SELECT pk.id, pk.key_value 
                FROM product_keys pk
                WHERE pk.product_id = ? AND pk.is_used = 0
                LIMIT ?
                """,
                    (base_product_id, card_count),
                )

                keys = cursor.fetchall()

                if len(keys) < card_count:
                    logger.error(
                        f"Недостаточно ключей для продукта '{item_name}'. Требуется: {card_count}, доступно: {len(keys)}"
                    )
                    continue

                # Формируем список ключей для этого заказа
                order_keys = []
                for key_id, key_value in keys:
                    # Отмечаем ключ как использованный и привязываем его к заказу
                    cursor.execute(
                        """
                    UPDATE product_keys
                    SET is_used = 1, order_id = ?, used_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                        (order_id, key_id),
                    )

                    order_keys.append({"key_id": key_id, "key_value": key_value})

                # Для комбинации карт привязываем к заказу только первый ключ
                if order_keys:
                    first_key_id = order_keys[0]["key_id"]

                    # Обновляем информацию о заказе
                    cursor.execute(
                        """
                    UPDATE orders
                    SET key_id = ?, key_sent_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                        (first_key_id, order_id),
                    )

                    # Формируем результат с информацией о всех ключах
                    keys_values = [k["key_value"] for k in order_keys]
                    result.append(
                        {
                            "order_id": order_id,
                            "product": item_name,
                            "key_count": len(keys_values),
                            "keys": keys_values,
                        }
                    )

                    logger.info(
                        f"Для заказа #{order_id} выделено {len(keys_values)} ключей"
                    )

        conn.commit()
        return result

    except Exception as e:
        logger.error(f"Ошибка при выделении ключей: {e}")
        conn.rollback()
        return []
    finally:
        conn.close()


def import_keys_from_files():
    """
    Импортирует ключи из текстовых файлов и добавляет их в базу данных.
    Roblox_10_usd.txt - для карт номиналом 10$
    Roblox_25_usd.txt - для карт номиналом 25$
    """

    # Проверка существования файлов
    files_to_process = []
    if keys_10_usd_file.exists():
        files_to_process.append(
            (
                keys_10_usd_file,
                "Карта поповнення Roblox Gift Card на 1000 ROBUX | 10$ (USD)",
            )
        )
    else:
        logger.error(f"Файл {keys_10_usd_file} не найден")

    if keys_25_usd_file.exists():
        files_to_process.append(
            (
                keys_25_usd_file,
                "Карта поповнення Roblox Gift Card на 2500 ROBUX | 25$ (USD)",
            )
        )
    else:
        logger.error(f"Файл {keys_25_usd_file} не найден")

    if not files_to_process:
        logger.error("Нет файлов для обработки")
        return

    # Подключаемся к базе данных
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    total_keys_added = 0

    try:
        for file_path, product_name in files_to_process:
            logger.info(f"Обработка файла {file_path} для продукта '{product_name}'")

            # Получаем ID продукта
            cursor.execute("SELECT id FROM products WHERE name = ?", (product_name,))
            product_data = cursor.fetchone()

            if not product_data:
                logger.error(f"Продукт '{product_name}' не найден в базе данных")
                continue

            product_id = product_data[0]
            keys_added = 0
            keys_skipped = 0

            # Читаем ключи из файла
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    key_value = line.strip()

                    # Пропускаем пустые строки
                    if not key_value:
                        continue

                    # Проверяем, существует ли уже такой ключ
                    cursor.execute(
                        "SELECT id FROM product_keys WHERE key_value = ?", (key_value,)
                    )
                    existing_key = cursor.fetchone()

                    if existing_key:
                        keys_skipped += 1
                        continue

                    # Добавляем новый ключ
                    cursor.execute(
                        """
                    INSERT INTO product_keys (product_id, key_value, is_used)
                    VALUES (?, ?, 0)
                    """,
                        (product_id, key_value),
                    )

                    keys_added += 1

            logger.info(
                f"Для продукта '{product_name}' добавлено {keys_added} ключей, пропущено {keys_skipped} ключей (уже существуют)"
            )
            total_keys_added += keys_added

            # Также обновляем JSON-файл с продуктами
            update_product_keys_in_json(product_name, key_value)

        conn.commit()
        logger.info(f"Всего добавлено {total_keys_added} ключей")

    except Exception as e:
        logger.error(f"Ошибка при импорте ключей: {e}")
        conn.rollback()
    finally:
        conn.close()


def update_product_keys_in_json(product_name, new_key=None):
    """
    Обновляет список ключей в JSON-файле с продуктами.
    Синхронизирует данные в JSON-файле с базой данных.

    Args:
        product_name (str): Название продукта
        new_key (str, optional): Новый ключ для добавления (если указан)
    """
    # Загружаем текущий JSON-файл с продуктами
    products_data = load_product_data(ROBLOX_PRODUCTS_FILE)
    if not products_data:
        logger.error(f"Не удалось загрузить данные из {ROBLOX_PRODUCTS_FILE}")
        return

    # Подключаемся к базе данных для получения актуальных ключей
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Получаем ID продукта
        cursor.execute("SELECT id FROM products WHERE name = ?", (product_name,))
        product_data = cursor.fetchone()

        if not product_data:
            logger.error(f"Продукт '{product_name}' не найден в базе данных")
            return

        product_id = product_data[0]

        # Получаем все ключи для этого продукта
        cursor.execute(
            """
        SELECT key_value FROM product_keys
        WHERE product_id = ? AND is_used = 0
        """,
            (product_id,),
        )

        keys = [row[0] for row in cursor.fetchall()]

        # Обновляем JSON-данные
        for product in products_data:
            if product["name"] == product_name:
                product["product_keys"] = keys
                break

        # Сохраняем обновленные данные в JSON-файл
        save_json_data(products_data, ROBLOX_PRODUCTS_FILE)
        logger.info(
            f"Обновлен список ключей для продукта '{product_name}' в {ROBLOX_PRODUCTS_FILE}"
        )

    except Exception as e:
        logger.error(f"Ошибка при обновлении JSON-файла: {e}")
    finally:
        conn.close()
