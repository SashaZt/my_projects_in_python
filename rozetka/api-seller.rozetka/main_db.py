# main_db.py
import asyncio
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
        email TEXT,
        first_name TEXT,
        last_name TEXT,
        second_name TEXT,
        full_name TEXT,
        created TEXT,
        amount TEXT,
        key_id INTEGER DEFAULT NULL,
        key_sent_at TEXT DEFAULT NULL,
        message_sent BOOLEAN DEFAULT 0,
        total_quantity INTEGER DEFAULT 1,
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

                    # # Добавляем ключи для этого продукта
                    # product_keys = product.get("product_keys", [])
                    # for key_value in product_keys:
                    #     # Проверяем, существует ли уже такой ключ
                    #     cursor.execute(
                    #         "SELECT id FROM product_keys WHERE key_value = ?",
                    #         (key_value,),
                    #     )
                    #     existing_key = cursor.fetchone()

                    #     if not existing_key:
                    #         # Добавляем новый ключ
                    #         cursor.execute(
                    #             """
                    #             INSERT INTO product_keys (product_id, key_value, is_used)
                    #             VALUES (?, ?, ?)
                    #             """,
                    #             (product_id, key_value, 0),
                    #         )
                    #         keys_added += 1

                conn.commit()
                # logger.info(
                #     f"Загружено {products_added} товаров и {keys_added} ключей из {ROBLOX_PRODUCTS_FILE}"
                # )
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
    # logger.info(f"- Товаров: {products_count}")
    # logger.info(f"- Ключей: {keys_count}")
    # logger.info(f"- Заказов: {orders_count}")

    conn.close()


init_db()


def save_parsed_orders_to_db(orders_data):
    """
    Сохраняет обработанные заказы в базу данных
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Добавляем или обновляем заказы
        for order in orders_data:
            order_id = order["order_id"]

            # Проверяем, существует ли заказ
            cursor.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
            existing_order = cursor.fetchone()

            if existing_order:
                # Обновляем существующий заказ
                cursor.execute(
                    """
                UPDATE orders SET 
                    item_name = ?, 
                    user_phone = ?, 
                    email = ?, 
                    full_name = ?, 
                    created = ?, 
                    amount = ?,
                    total_quantity = ?,
                    status = ?
                WHERE id = ?
                """,
                    (
                        order["product"],
                        order["user_phone"],
                        order["email"],
                        order.get("full_name", ""),
                        order.get("created", ""),
                        order.get("amount", ""),
                        order.get("total_quantity", 1),
                        7,  # Статус 7 - "оплачено"
                        order_id,
                    ),
                )
            else:
                # Добавляем новый заказ
                cursor.execute(
                    """
                INSERT INTO orders 
                (id, item_name, user_phone, email, full_name, created, amount, status, total_quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        order_id,
                        order["product"],
                        order["user_phone"],
                        order["email"],
                        order.get("full_name", ""),
                        order.get("created", ""),
                        order.get("amount", ""),
                        7,  # Статус 7 - "оплачено" вместо 1
                        order.get("total_quantity", 1),
                    ),
                )

        conn.commit()
        logger.info(f"Сохранено {len(orders_data)} заказов в БД")

    except Exception as e:
        logger.error(f"Ошибка при сохранении заказов в БД: {e}")
    finally:
        if conn:
            conn.close()


def get_next_available_key_for_orders():
    """
    Проверяет таблицу заказов на наличие заказов без отправленных ключей,
    выделяет для них ключи и отмечает их как использованные.
    Учитывает total_quantity - количество единиц товара в заказе.
    """
    conn = sqlite3.connect(DB_NAME)
    # Включаем поддержку внешних ключей
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        # Получаем заказы, для которых еще не были отправлены ключи
        # Добавляем в выборку total_quantity
        cursor.execute(
            """
        SELECT o.id, o.item_name, o.status, o.user_phone, o.email, o.full_name, o.total_quantity
        FROM orders o
        WHERE o.key_sent_at IS NULL AND o.status = 7  -- статус 7 обычно означает "оплачено"
        """
        )

        orders_without_keys = cursor.fetchall()

        if not orders_without_keys:
            logger.info("Нет заказов, требующих выделения ключей")
            return []

        result = []

        # Получаем информацию о доступных картах 10$ и 25$
        cursor.execute(
            """
        SELECT p.id, p.name 
        FROM products p 
        WHERE p.name = 'Карта поповнення Roblox Gift Card на 1000 ROBUX | 10$ (USD)'
        """
        )
        card_10_info = cursor.fetchone()

        cursor.execute(
            """
        SELECT p.id, p.name 
        FROM products p 
        WHERE p.name = 'Карта поповнення Roblox Gift Card на 2500 ROBUX | 25$ (USD)'
        """
        )
        card_25_info = cursor.fetchone()

        if not card_10_info:
            logger.error("Базовая карта 10$ не найдена в базе данных")
            return []

        if not card_25_info:
            logger.error("Базовая карта 25$ не найдена в базе данных")
            # Продолжаем работу, так как некоторые заказы могут требовать только карты 10$

        card_10_id = card_10_info[0]
        card_25_id = card_25_info[0] if card_25_info else None

        for order_data in orders_without_keys:
            # Добавляем total_quantity в распаковку
            (
                order_id,
                item_name,
                status,
                user_phone,
                email,
                full_name,
                total_quantity,
            ) = order_data

            # Если total_quantity не задано или равно 0, устанавливаем 1
            total_quantity = total_quantity if total_quantity else 1
            logger.info(
                f"Заказ #{order_id} содержит {total_quantity} единиц товара '{item_name}'"
            )

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

            # Учитываем total_quantity - умножаем необходимое количество карт на количество товара
            required_card_count = card_count * total_quantity
            logger.info(
                f"Требуется {required_card_count} ключей для заказа #{order_id}"
            )

            # Определяем, какой базовый продукт использовать
            base_product_id = None
            if card_value == 10:
                base_product_id = card_10_id
            elif card_value == 25:
                base_product_id = card_25_id
            else:
                logger.error(f"Неизвестный номинал карты: {card_value}$")
                continue

            # Проверяем наличие достаточного количества ключей
            cursor.execute(
                """
            SELECT COUNT(id) 
            FROM product_keys 
            WHERE product_id = ? AND is_used = 0
            """,
                (base_product_id,),
            )

            available_keys_count = cursor.fetchone()[0]

            if available_keys_count < required_card_count:
                logger.error(
                    f"Недостаточно ключей для продукта '{item_name}'. Требуется: {required_card_count}, доступно: {available_keys_count}"
                )
                # Добавляем информацию о проблеме в результат
                result.append(
                    {
                        "order_id": order_id,
                        "product": item_name,
                        "user_phone": user_phone,
                        "email": email,
                        "full_name": full_name,
                        "key_count": 0,
                        "keys": [],
                        "key_ids": [],
                        "total_quantity": total_quantity,
                        "error": f"Недостаточно ключей. Требуется: {required_card_count}, доступно: {available_keys_count}",
                    }
                )
                continue

            # Получаем необходимое количество ключей (с учетом total_quantity)
            cursor.execute(
                """
            SELECT id, key_value 
            FROM product_keys 
            WHERE product_id = ? AND is_used = 0
            LIMIT ?
            """,
                (base_product_id, required_card_count),
            )

            keys = cursor.fetchall()

            # Формируем список ключей для этого заказа и отмечаем их как использованные
            keys_list = []
            key_ids = []
            for key_id, key_value in keys:
                # Отмечаем ключ как использованный и привязываем его к заказу
                cursor.execute(
                    """
                UPDATE product_keys
                SET is_used = 1, order_id = ?
                WHERE id = ?
                """,
                    (order_id, key_id),
                )

                keys_list.append(key_value)
                key_ids.append(key_id)

            # Обновляем информацию о заказе, устанавливая первый ключ и время отправки
            if key_ids:
                cursor.execute(
                    """
                UPDATE orders
                SET key_id = ?
                WHERE id = ?
                """,
                    (key_ids[0], order_id),
                )

            # Добавляем информацию о заказе и найденных ключах в результат
            result.append(
                {
                    "order_id": order_id,
                    "product": item_name,
                    "user_phone": user_phone,
                    "email": email,
                    "full_name": full_name,
                    "key_count": len(keys_list),
                    "keys": keys_list,
                    "key_ids": key_ids,
                    "total_quantity": total_quantity,  # Добавляем total_quantity в результат
                }
            )

        # Фиксируем изменения в базе данных
        conn.commit()

        return result

    except Exception as e:
        logger.error(f"Ошибка при выделении ключей: {e}")
        conn.rollback()  # Откатываем изменения в случае ошибки
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

    logger.info(files_to_process)
    # Убрано exit() для продолжения выполнения функции

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
                    logger.info(f"Ключ добавлен {key_value}")
                    keys_added += 1

            total_keys_added += keys_added
            logger.info(
                f"Добавлено {keys_added} ключей для продукта '{product_name}', пропущено {keys_skipped} дубликатов"
            )

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


def mark_keys_as_sent(order_id, key_ids):
    """
    Отмечает ключи как отправленные и связывает их с заказом после успешной отправки сообщения.

    Args:
        order_id (int): ID заказа
        key_ids (list): Список ID ключей, которые были отправлены
    """
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        # Отмечаем ключи как использованные
        for key_id in key_ids:
            cursor.execute(
                """
            UPDATE product_keys
            SET is_used = 1, order_id = ?, used_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
                (order_id, key_id),
            )

        # Устанавливаем первый ключ как основной для заказа и обновляем статус заказа
        if key_ids:
            cursor.execute(
                """
            UPDATE orders
            SET key_id = ?, key_sent_at = CURRENT_TIMESTAMP, message_sent = 1
            WHERE id = ?
            """,
                (key_ids[0], order_id),
            )

        conn.commit()
        logger.info(f"Ключи {key_ids} отмечены как отправленные для заказа #{order_id}")

        return True
    except Exception as e:
        logger.error(f"Ошибка при отметке ключей как отправленных: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
