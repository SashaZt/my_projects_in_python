# src/main_bd.py
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from config_utils import load_config
from logger import logger

config = load_config()
BASE_DIR = Path(__file__).parent.parent  # Для модулей в папке src
db_path = BASE_DIR / config["files"]["db_file"]

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
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создаем таблицу с англоязычными именами колонок
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_slug TEXT UNIQUE,
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

    # logger.info("База данных с англоязычными колонками успешно создана")


def insert_data_from_json(json_data):
    """
    Записывает данные из JSON в базу данных с преобразованием имен полей
    Если запись с product_slug уже существует, обновляет все данные
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем текущую дату и время
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Если json_data - строка, преобразуем в объект Python
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    # Счетчики для статистики
    inserted_count = 0
    updated_count = 0
    error_count = 0

    for item in data:
        try:
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

            # Проверяем, существует ли запись с таким product_slug
            product_slug = item_eng.get("product_slug")
            if not product_slug:
                logger.warning("Пропущена запись без product_slug")
                error_count += 1
                continue

            # Проверяем, есть ли уже такой product_slug в базе
            cursor.execute(
                "SELECT COUNT(*) FROM products WHERE product_slug = ?", (product_slug,)
            )
            exists = cursor.fetchone()[0] > 0

            if exists:
                # Если запись существует, обновляем все данные
                update_parts = []
                update_values = []

                for key, value in item_eng.items():
                    if key != "product_slug":  # Не обновляем сам product_slug
                        update_parts.append(f'"{key}" = ?')
                        update_values.append(value)

                # Добавляем product_slug для условия WHERE
                update_values.append(product_slug)

                # Создаем SQL запрос для обновления
                update_query = f"""
                UPDATE products 
                SET {", ".join(update_parts)}
                WHERE product_slug = ?
                """

                cursor.execute(update_query, update_values)
                updated_count += 1
                # logger.debug(f"Обновлена запись с product_slug: {product_slug}")
            else:
                # Если записи нет, добавляем новую
                columns = ", ".join([f'"{k}"' for k in item_eng.keys()])
                placeholders = ", ".join(["?"] * len(item_eng))
                values = list(item_eng.values())

                insert_query = (
                    f"INSERT INTO products ({columns}) VALUES ({placeholders})"
                )
                cursor.execute(insert_query, values)
                inserted_count += 1
                logger.debug(f"Добавлена новая запись с product_slug: {product_slug}")

        except sqlite3.Error as e:
            logger.error(f"Ошибка при обработке записи: {e}")
            error_count += 1
            continue

    conn.commit()
    conn.close()

    logger.info("Обработка JSON данных завершена")
    logger.info(f"- Новых записей добавлено: {inserted_count}")
    logger.info(f"- Существующих записей обновлено: {updated_count}")
    logger.info(f"- Записей с ошибками: {error_count}")
    logger.info(f"- Всего обработано записей: {len(data)}")


# Добавить параметр category_id в функцию get_product_data
def get_product_data(category_id=None):
    """
    Возвращает product_slug, product_code и price из базы данных

    Args:
        category_id (str, optional): ID категории для фильтрации

    Returns:
        list: Список словарей с product_slug, product_code и price
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Если указан category_id, добавляем условие фильтрации
    if category_id:
        query = "SELECT product_slug, product_code, price FROM products WHERE group_number = ?"
        cursor.execute(query, (category_id,))
    else:
        # Иначе выбираем все записи
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


def update_prices_and_images(json_file_path, category_id=None):
    """
    Обновляет цены и добавляет изображения в базу данных на основе предоставленных данных

    Args:
        json_file_path (str or Path): Путь к JSON-файлу с данными
        category_id (str, optional): ID категории для фильтрации

    Returns:
        tuple: (updated_prices, updated_images, errors) - количество обновлений цен, изображений и ошибок
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updated_prices = 0
    updated_images = 0
    errors = 0

    # Загружаем данные из JSON-файла
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    for item in data:
        slug = item.get("slug")
        price = item.get("price")
        images = item.get("images", [])

        if not slug:
            logger.error("Пропущена запись без slug")
            errors += 1
            continue

        try:
            # Проверяем существование записи (с учетом категории, если указана)
            if category_id:
                query = "SELECT product_slug, image_url FROM products WHERE product_slug = ? AND group_number = ?"
                cursor.execute(query, (slug, category_id))
            else:
                cursor.execute(
                    "SELECT product_slug, image_url FROM products WHERE product_slug = ?",
                    (slug,),
                )
            result = cursor.fetchone()

            if not result:
                logger.warning(f"Запись с product_slug={slug} не найдена в базе данных")
                errors += 1
                continue

            # Получаем текущее значение image_url
            current_image_url = result[1] or ""

            # Обновляем цену, даже если она null - устанавливаем "0"
            if price is not None:
                price_str = str(price).replace(".", ",")
            else:
                price_str = "0"  # Если price = null, устанавливаем "0"

            # Если цена "0", также обновляем availability на "-"
            if price_str == "0":
                cursor.execute(
                    "UPDATE products SET price = ?, availability = ? WHERE product_slug = ?",
                    (price_str, "-", slug),
                )
                logger.debug(
                    f"Обновлена цена для {slug}: {price_str} и availability: '-'"
                )
            else:
                cursor.execute(
                    "UPDATE products SET price = ? WHERE product_slug = ?",
                    (price_str, slug),
                )
                logger.debug(f"Обновлена цена для {slug}: {price_str}")

            updated_prices += 1

            # Обновляем изображения, если они предоставлены
            if images:
                # Преобразуем список URL в строку с разделителями
                images_str = ", ".join(images)

                # Если уже есть изображения, добавляем новые через запятую
                if current_image_url and current_image_url.strip():
                    # Проверяем, не содержит ли текущее поле уже эти ссылки
                    existing_urls = [
                        url.strip() for url in current_image_url.split(",")
                    ]
                    new_urls = []

                    for url in images:
                        if url not in existing_urls:
                            new_urls.append(url)

                    if new_urls:
                        # Добавляем только новые URL
                        combined_urls = current_image_url + ", " + ", ".join(new_urls)
                        cursor.execute(
                            "UPDATE products SET image_url = ? WHERE product_slug = ?",
                            (combined_urls, slug),
                        )
                        updated_images += 1
                        logger.debug(
                            f"Добавлены новые изображения для {slug}: {len(new_urls)} шт."
                        )
                else:
                    # Если изображений нет, просто устанавливаем новые
                    cursor.execute(
                        "UPDATE products SET image_url = ? WHERE product_slug = ?",
                        (images_str, slug),
                    )
                    updated_images += 1
                    logger.debug(
                        f"Установлены изображения для {slug}: {len(images)} шт."
                    )

        except sqlite3.Error as e:
            logger.error(f"Ошибка при обновлении записи {slug}: {str(e)}")
            errors += 1
            continue

    conn.commit()
    conn.close()

    logger.info(f"Обновление данных завершено:")
    logger.info(f"- Обновлено цен: {updated_prices}")
    logger.info(f"- Обновлено изображений: {updated_images}")
    logger.info(f"- Ошибок: {errors}")

    return updated_prices, updated_images, errors


def get_all_data_ukrainian_headers(category_id=None):
    """
    Возвращает все данные из базы данных, кроме id и product_slug,
    с украинскими названиями заголовков

    Args:
        category_id (str, optional): ID категории для фильтрации

    Returns:
        list: Список словарей с данными с украинскими ключами
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем информацию о структуре таблицы
    cursor.execute("PRAGMA table_info(products)")
    columns_info = cursor.fetchall()

    # Формируем список колонок, исключая id и product_slug
    columns = [
        column[1]
        for column in columns_info
        if column[1] not in ["id", "product_slug", "upload_date"]
    ]

    # # Проверяем наличие поля discount в списке колонок
    # if "discount" not in columns:
    #     logger.warning("Поле 'discount' отсутствует в структуре таблицы")
    # else:
    #     logger.debug("Поле 'discount' найдено в структуре таблицы")

    # Создаем обратное отображение (с английского на украинский)
    reverse_mapping = {v: k for k, v in FIELD_MAPPING.items()}

    # # Проверяем маппинг для поля discount
    # if "discount" in reverse_mapping:
    #     logger.debug(f"Маппинг для 'discount': {reverse_mapping['discount']}")
    # else:
    #     logger.warning("Поле 'discount' отсутствует в обратном маппинге")

    # Выполняем запрос с возможной фильтрацией по категории
    if category_id:
        query = f"SELECT {', '.join(columns)} FROM products WHERE group_number = ?"
        cursor.execute(query, (category_id,))
    else:
        query = f"SELECT {', '.join(columns)} FROM products"
        cursor.execute(query)

    rows = cursor.fetchall()

    # Преобразуем результат в список словарей с украинскими ключами
    result = []
    for row in rows:
        item = {}
        for i, column in enumerate(columns):
            # Если есть соответствующий украинский ключ, используем его
            ukrainian_key = reverse_mapping.get(column, column)
            item[ukrainian_key] = row[i]

            # # Проверяем специально поле discount
            # if column == "discount":
            #     logger.debug(
            #         f"Обработка поля 'discount': '{row[i]}' -> '{ukrainian_key}'"
            #     )

        result.append(item)

    conn.close()

    logger.info(
        f"Получено {len(result)} записей из базы данных с украинскими заголовками"
    )
    return result


def update_unique_ids_in_db(id_mapping):
    """
    Обновляет значения unique_id в базе данных

    Args:
        id_mapping (dict): Словарь с product_code в качестве ключа и unique_id в качестве значения

    Returns:
        tuple: (обновлено, ошибок)
    """
    if not id_mapping:
        logger.error("Пустой словарь ID для обновления")
        return 0, 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updated = 0
    errors = 0
    not_found = 0

    # Проверяем существование таблицы
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
    )
    if not cursor.fetchone():
        logger.error("Таблица 'products' не существует в базе данных")
        conn.close()
        return 0, 0

    # Проверяем существование колонок
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]

    if "product_name" not in columns or "unique_id" not in columns:
        logger.error("Необходимые колонки не найдены в таблице 'products'")
        conn.close()
        return 0, 0

    # Создаем словарь существующих кодов товаров для оптимизации запросов
    cursor.execute("SELECT product_name FROM products")
    existing_codes = set(row[0] for row in cursor.fetchall() if row[0])

    # Обновляем unique_id для каждого product_code
    for product_name, unique_id in id_mapping.items():
        try:
            # Здесь product_name уже в нижнем регистре из предыдущей функции
            if product_name in existing_codes:
                # Но в запросе используем LOWER для сравнения с БД
                cursor.execute(
                    "UPDATE products SET unique_id = ? WHERE LOWER(product_name) = ?",
                    (unique_id, product_name),
                )

                if cursor.rowcount > 0:
                    updated += 1
                    if updated % 100 == 0:  # Логируем каждые 100 обновлений
                        logger.info(f"Обновлено записей: {updated}")
                else:
                    not_found += 1
            else:
                not_found += 1
                if not_found % 100 == 0:  # Логируем каждые 100 не найденных
                    logger.warning(f"Код товара не найден в БД: {product_name}")

        except sqlite3.Error as e:
            logger.error(
                f"Ошибка при обновлении записи с кодом {product_name}: {str(e)}"
            )
            errors += 1

    conn.commit()
    conn.close()

    logger.info("Обновление уникальных идентификаторов завершено:")
    logger.info(f"- Обновлено записей: {updated}")
    logger.info(f"- Не найдено кодов товаров: {not_found}")
    logger.info(f"- Ошибок: {errors}")

    return updated, errors
