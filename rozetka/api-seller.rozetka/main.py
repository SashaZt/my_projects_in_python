import base64
import json
import sqlite3
import sys
from pathlib import Path

import requests
from loguru import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
db_directory = current_directory / "db"
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
db_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

access_token_json_file = data_directory / "access_token.json"
orders_json_file = data_directory / "orders.json"
output_xlsx_file = data_directory / "output.xlsx"
output_csv_file = data_directory / "output.csv"
output_xml_file = data_directory / "output.xml"
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

# Конфигурация
USERNAME = "testrozetka1"  # Замените на свой логин
PASSWORD = "SashaZt83"  # Замените на свой пароль
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


def load_product_data(file_path):
    """Загрузка данных товара из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных товара: {e}")
        return None


# Авторизация и получение токена
def get_auth_token():
    url = "https://api-seller.rozetka.com.ua/sites"

    # Кодируем пароль в base64
    password_base64 = base64.b64encode(PASSWORD.encode()).decode()

    payload = {"username": USERNAME, "password": password_base64}

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if response.status_code == 200:
        data = response.json()
        success = data["success"]
        if success:
            with open(access_token_json_file, "w", encoding="utf-8") as json_file:
                json.dump(
                    data["content"]["access_token"],
                    json_file,
                    ensure_ascii=False,
                    indent=4,
                )
        else:
            logger.error(
                f"Ошибка авторизации: {data.get('errors', {}).get('message', 'Неизвестная ошибка')}"
            )
            return None
    else:
        logger.error(f"Ошибка HTTP: {response.status_code}")
        return None


# Получение заказов
def get_orders(token):
    url = "https://api-seller.rozetka.com.ua/orders/search"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Можно добавить параметры для фильтрации заказов
    params = {
        # "status": "1",  # статус заказа
        # "date_from": "2023-01-01",  # дата начала
        # "date_to": "2023-12-31",  # дата окончания
        "page": 1,  # страница
        "per_page": 20,  # количество заказов на странице
    }

    response = requests.get(url, headers=headers, params=params, timeout=30)

    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            return data["content"]["orders"]
        else:
            logger.error(
                f"Ошибка получения заказов: {data.get('errors', {}).get('message', 'Неизвестная ошибка')}"
            )
            return []
    else:
        logger.error(f"Ошибка HTTP: {response.status_code}")
        return []


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
    main()
