import json
import sqlite3
import sys
from pathlib import Path

import requests
from loguru import logger
from main_token import get_token, load_product_data, save_json_data, validyty_token

current_directory = Path.cwd()
data_directory = current_directory / "data"
db_directory = current_directory / "db"
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
db_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

access_token_json_file = data_directory / "access_token.json"
orders_json_file = data_directory / "orders.json"
roblox_products_json_file = data_directory / "roblox_products.json"
output_xlsx_file = data_directory / "output.xlsx"
output_csv_file = data_directory / "output.csv"
output_xml_file = data_directory / "output.xml"
log_file_path = log_directory / "log_message.log"
config_json_file = data_directory / "config.json"

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


DB_NAME = db_directory / "rozetka_orders.db"
ROBLOX_PRODUCTS_FILE = data_directory / "roblox_products.json"


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

    # Загружаем товары из JSON-файла, если он существует
    if ROBLOX_PRODUCTS_FILE.exists():
        try:
            with open(ROBLOX_PRODUCTS_FILE, "r", encoding="utf-8") as file:
                products = json.load(file)

                # Добавляем товары в базу данных
                for product in products:
                    # Извлекаем значения robux и usd из имени товара
                    name = product["name"]
                    logger.info(name)
                    # Вставляем товар в базу данных
                    cursor.execute(
                        "INSERT OR IGNORE INTO products (name) VALUES (?)", (name,)
                    )

                logger.info(
                    f"Загружено {len(products)} товаров из {ROBLOX_PRODUCTS_FILE}"
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


# Сохранение заказов в базу данных
def save_orders_to_db(orders):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    orders = orders["content"]["orders"]
    for order in orders:
        # Извлекаем нужные поля
        order_id = order["id"]
        status = order["status"]
        created = order["created"]
        amount = order["amount"]

        # Извлекаем информацию о товаре (берем первый товар, если их несколько)
        item_name = (
            order["items_photos"][0]["item_name"] if order["items_photos"] else ""
        )

        # Извлекаем информацию о пользователе
        user_phone = order["user_phone"]
        user_info = order["user_title"]
        first_name = user_info.get("first_name", "")
        last_name = user_info.get("last_name", "")
        second_name = user_info.get("second_name", "")
        full_name = user_info.get("full_name", "")

        # Проверяем, существует ли уже такой заказ
        cursor.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
        existing_order = cursor.fetchone()

        if existing_order:
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

    conn.commit()

    # Выводим количество записей в базе
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    logger.info(f"В базе данных {count} заказов")

    conn.close()


def make_api_request(method, url, params=None, data=None):
    """
    Универсальная функция для выполнения API запросов

    Args:
        method (str): HTTP метод (GET, POST и т.д.)
        url (str): URL для запроса
        params (dict, optional): Параметры запроса
        data (dict, optional): Данные для отправки в теле запроса

    Returns:
        dict or None: Результат запроса или None в случае ошибки
    """
    # Получаем токен (функция get_token() из main_token.py проверяет все возможные источники)
    token = get_token()
    if not token:
        logger.error("Токен не найден, запустите validyty_token() из main_token.py")
        return None

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        logger.info(f"Выполнение {method} запроса к {url}")
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=30,
        )

        # Проверяем статус HTTP
        response.raise_for_status()

        # Парсим ответ
        result = response.json()

        if not result.get("success"):
            error_msg = result.get("errors", {}).get("message", "")
            error_code = result.get("errors", {}).get("code", 0)
            logger.error(f"API вернул ошибку: {error_msg} (код {error_code})")
            return None

        return result
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP ошибка: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")
        return None


def get_orders():
    """Получение списка заказов"""
    url = "https://api-seller.rozetka.com.ua/orders/search"
    params = {
        # "status": "1",  # статус заказа
        # "date_from": "2023-01-01",  # дата начала
        # "date_to": "2023-12-31",  # дата окончания
        "page": 1,  # страница
        "per_page": 20,  # количество заказов на странице
    }

    result = make_api_request("GET", url, params)
    if result and result.get("success"):
        # Сохраняем полученные заказы в файл
        save_json_data(result, orders_json_file)
        return result["content"]["orders"]

    logger.error("Не удалось получить список заказов")
    return []


def get_status_payment(order_id):
    """Получение статуса платежа по ID заказа"""
    url = f"https://api-seller.rozetka.com.ua/orders/status-payment/{order_id}"

    result = make_api_request("GET", url)
    logger.info(result)

    if result and result.get("success"):
        # Проверяем, что content не None перед доступом к его атрибутам
        if result.get("content") is not None:
            status_payment_id = result["content"].get("status_payment_id")
            if status_payment_id == 7:
                # Сохраняем статус платежа в файл для отладки
                status_file = data_directory / f"status_payment_{order_id}.json"
                save_json_data(result, status_file)
                return result["content"]

    logger.error(f"Не удалось получить статус платежа для заказа {order_id}")
    return None


def process_orders():
    """Обработка заказов и выборка нужной информации"""
    # Запускаем проверку валидности токена
    validyty_token()

    # Получаем заказы
    orders_data = get_orders()
    if not orders_data:
        logger.error("Нет данных о заказах для обработки")
        return []

    # Загружаем список товаров
    products_data = load_product_data(roblox_products_json_file)
    if not products_data:
        logger.error("Не удалось загрузить данные о товарах")
        return []

    # Создаем список только имен товаров для удобства проверки
    product_names = [product["name"] for product in products_data]

    result = []
    logger.info(f"Обработка {len(orders_data)} заказов")

    for order in orders_data:
        try:
            # Извлекаем информацию о товаре (первый товар в заказе)
            if not order.get("items_photos") or len(order["items_photos"]) == 0:
                logger.warning(
                    f"Заказ {order.get('id')} не содержит информации о товарах"
                )
                continue

            item_name = order["items_photos"][0]["item_name"]

            # Проверяем, что товар есть в нашем списке
            if item_name in product_names:
                order_id = order["id"]
                logger.info(f"Обработка заказа #{order_id} - {item_name}")

                # Получаем статус платежа
                payment_status = get_status_payment(order_id)
                logger.info(payment_status)
                user_phone = None
                payment_status_title = "Не оплачено"  # Значение по умолчанию

                if payment_status is not None:
                    logger.info(payment_status)
                    payment_status_title = payment_status.get("title", "Не оплачено")

                    # Если статус "Сума заблокована", сохраняем телефон
                    if payment_status_title == "Сума заблокована":
                        user_phone = order["user_phone"]
                        logger.info(
                            f"Сумма заблокирована для заказа #{order_id}, телефон: {user_phone}"
                        )
                else:
                    logger.info("Не оплачено")
                # Формируем данные заказа
                all_data = {
                    "order_id": order_id,
                    "product": item_name,
                    "user_phone": user_phone,
                    "status": order["status"],
                    "status_payment": payment_status_title,
                    "created": order["created"],
                    "amount": order["amount"],
                    "user_info": {
                        "first_name": order["user_title"].get("first_name", ""),
                        "last_name": order["user_title"].get("last_name", ""),
                        "full_name": order["user_title"].get("full_name", ""),
                    },
                }
                result.append(all_data)
            else:
                logger.info(f"Товар {item_name} не наш")
        except Exception as e:
            logger.error(f"Ошибка при обработке заказа {order.get('id')}: {e}")

    # Сохраняем результат обработки
    result_file = data_directory / "parsed_orders.json"
    save_json_data(result, result_file)
    logger.info(f"Обработано {len(result)} заказов")

    return result


# Главная функция
def main():
    # Инициализация базы данных
    init_db()

    # Получение токена авторизации
    # get_auth_token()
    # token = load_product_data(access_token_json_file)
    # # Получение заказов

    # orders = get_orders(token)
    # if not orders:
    #     logger.error("Заказы не найдены или произошла ошибка")
    #     return
    # orders = load_product_data(orders_json_file)
    # # Сохранение заказов в базу данных
    # save_orders_to_db(orders)
    # logger.info(f"Обработано {len(orders)} заказов")


if __name__ == "__main__":
    # main()
    process_orders()
