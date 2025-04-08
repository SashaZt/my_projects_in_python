import json
import re
import sqlite3
from datetime import datetime

from logger import logger

# Словарь соответствия украинских имен полей и английских
FIELD_MAPPING = {
    "product_slug": "product_slug",
    "Код_товару": "product_code",
    "Назва_позиції": "product_name",
    "Назва_позиції_укр": "product_name_ukr",
    "Пошукові_запити": "search_queries",
    "Пошукові_запити_укр": "search_queries_ukr",
    "Опис": "description",
    "Опис_укр": "description_ukr",
    "Тип_товару": "product_type",
    "Ціна": "price",
    "Валюта": "currency",
    "Одиниця_виміру": "unit",
    "Мінімальний_обсяг_замовлення": "min_order_volume",
    "Оптова_ціна": "wholesale_price",
    "Мінімальне_замовлення_опт": "min_wholesale_order",
    "Посилання_зображення": "image_url",
    "Наявність": "availability",
    "Кількість": "quantity",
    "Номер_групи": "group_number",
    "Назва_групи": "group_name",
    "Посилання_підрозділу": "section_url",
    "Можливість_поставки": "delivery_option",
    "Термін_поставки": "delivery_time",
    "Спосіб_пакування": "packaging",
    "Спосіб_пакування_укр": "packaging_ukr",
    "Унікальний_ідентифікатор": "unique_id",
    "Ідентифікатор_товару": "product_id",
    "Ідентифікатор_підрозділу": "department_id",
    "Ідентифікатор_групи": "group_id",
    "Виробник": "manufacturer",
    "Країна_виробник": "country",
    "Знижка": "discount",
    "ID_групи_різновидів": "variety_group_id",
    "Особисті_нотатки": "personal_notes",
    "Продукт_на_сайті": "product_on_site",
    "Термін_дії_знижки_від": "discount_valid_from",
    "Термін_дії_знижки_до": "discount_valid_to",
    "Ціна_від": "price_from",
    "Ярлик": "label",
    "HTML_заголовок": "html_title",
    "HTML_заголовок_укр": "html_title_ukr",
    "HTML_опис": "html_description",
    "HTML_опис_укр": "html_description_ukr",
    "Код_маркування_(GTIN)": "gtin_code",
    "Номер_пристрою_(MPN)": "mpn_number",
    "Вага,кг": "weight_kg",
    "Ширина,см": "width_cm",
    "Висота,см": "height_cm",
    "Довжина,см": "length_cm",
    "Де_знаходиться_товар": "item_location",
    "Назва_Характеристики": "characteristic_name",
    "Одиниця_виміру_Характеристики": "characteristic_unit",
    "Значення_Характеристики": "characteristic_value",
    "дата_загрузки": "upload_date",
}


def create_database():
    """
    Создает базу данных с англоязычными именами колонок
    """
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()

    # Создаем таблицу с англоязычными именами колонок
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_slug TEXT,
        product_code TEXT,
        product_name TEXT,
        product_name_ukr TEXT,
        search_queries TEXT,
        search_queries_ukr TEXT,
        description TEXT,
        description_ukr TEXT,
        product_type TEXT,
        price TEXT,
        currency TEXT,
        unit TEXT,
        min_order_volume TEXT,
        wholesale_price TEXT,
        min_wholesale_order TEXT,
        image_url TEXT,
        availability TEXT,
        quantity TEXT,
        group_number TEXT,
        group_name TEXT,
        section_url TEXT,
        delivery_option TEXT,
        delivery_time TEXT,
        packaging TEXT,
        packaging_ukr TEXT,
        unique_id TEXT,
        product_id TEXT,
        department_id TEXT,
        group_id TEXT,
        manufacturer TEXT,
        country TEXT,
        discount TEXT,
        variety_group_id TEXT,
        personal_notes TEXT,
        product_on_site TEXT,
        discount_valid_from TEXT,
        discount_valid_to TEXT,
        price_from TEXT,
        label TEXT,
        html_title TEXT,
        html_title_ukr TEXT,
        html_description TEXT,
        html_description_ukr TEXT,
        gtin_code TEXT,
        mpn_number TEXT,
        weight_kg TEXT,
        width_cm TEXT,
        height_cm TEXT,
        length_cm TEXT,
        item_location TEXT,
        characteristic_name TEXT,
        characteristic_unit TEXT,
        characteristic_value TEXT,
        upload_date DATETIME
    )
    """
    )

    conn.commit()
    conn.close()

    logger.info("База данных с англоязычными колонками успешно создана")


def insert_data_from_json(json_data):
    """
    Записывает данные из JSON в базу данных с преобразованием имен полей
    """
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()

    # Получаем текущую дату и время
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Если json_data - строка, преобразуем в объект Python
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    for item in data:
        # Преобразуем ключи с украинского на английский
        item_eng = {}
        for key, value in item.items():
            # Преобразуем ключ в английский эквивалент или используем оригинальный ключ
            eng_key = FIELD_MAPPING.get(key, key)
            # Заменяем все специальные символы в ключе
            eng_key = re.sub(r"[^\w]", "_", eng_key)
            item_eng[eng_key] = value

        # Добавляем дату загрузки
        item_eng["upload_date"] = current_datetime

        # Формируем плейсхолдеры для SQL-запроса
        placeholders = ", ".join(["?"] * len(item_eng))

        # Формируем имена столбцов
        columns = ", ".join([f'"{k}"' for k in item_eng.keys()])

        # Формируем значения для вставки
        values = list(item_eng.values())

        # Выполняем запрос
        query = f"INSERT INTO products ({columns}) VALUES ({placeholders})"
        try:
            cursor.execute(query, values)
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении записи: {e}")
            logger.error(f"Запрос: {query}")
            logger.error(f"Колонки: {columns}")
            # Продолжаем выполнение, пропуская проблемную запись
            continue

    conn.commit()
    conn.close()

    logger.info(f"Данные успешно загружены в базу данных. Всего записей: {len(data)}")


def get_product_data():
    """
    Возвращает product_slug, product_code и price из базы данных
    """
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()

    cursor.execute("SELECT product_slug, product_code, price FROM products")
    result = cursor.fetchall()

    # Преобразуем результат в список словарей
    data = [
        {"product_slug": row[0], "product_code": row[1], "price": row[2]}
        for row in result
    ]

    conn.close()

    return data


def map_json_to_english(json_data):
    """
    Преобразует JSON с украинскими ключами в JSON с английскими ключами
    """
    # Если json_data - строка, преобразуем в объект Python
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    result = []
    for item in data:
        item_eng = {}
        for key, value in item.items():
            # Ищем английский эквивалент для ключа
            eng_key = FIELD_MAPPING.get(key, key)
            item_eng[eng_key] = value
        result.append(item_eng)

    return result


def load_and_save_data(json_file_path):
    """
    Загружает данные из JSON-файла и сохраняет их в базу данных
    """
    # Создаем базу данных, если не существует
    create_database()

    # Загружаем данные из JSON-файла
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Вставляем данные в базу данных
    insert_data_from_json(data)

    logger.info(f"Данные из {json_file_path} успешно загружены в базу данных")


def reverse_map_to_ukrainian(data):
    """
    Преобразует данные с английскими ключами обратно в данные с украинскими ключами
    """
    # Создаем обратное отображение (с английского на украинский)
    reverse_mapping = {v: k for k, v in FIELD_MAPPING.items()}

    result = []
    for item in data:
        item_ukr = {}
        for key, value in item.items():
            # Ищем украинский эквивалент для ключа
            ukr_key = reverse_mapping.get(key, key)
            item_ukr[ukr_key] = value
        result.append(item_ukr)

    return result


# # Пример использования

# if __name__ == "__main__":
#     # Пример 1: Создание базы данных и загрузка данных
#     # load_and_save_data('bd_json.json')

#     # Пример 2: Получение данных из базы
#     # product_data = get_product_data()
#     # print(product_data)
