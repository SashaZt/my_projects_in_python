import json
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from logger import logger

def connect_to_db():
    """Установка соединения с базой данных"""
    conn = psycopg2.connect(
        host="10.0.0.18",
        port="5430",
        database="auto_parts_database",
        user="auto_parts_database_user",
        password="auto_parts_database_password",
    )
    return conn

def extract_car_info_from_path(file_path):
    """Извлечение информации о категории, марке и модели автомобиля из пути к файлу"""
    path = Path(file_path)
    
    try:
        parts = path.parts
        if len(parts) < 4:
            logger.warning(f"Недостаточно компонентов в пути: {file_path}")
            return None, None, None

        selectedcategoryid = parts[-4]  # 255099
        brandcar = parts[-3]  # audi
        model_dir = parts[-2]  # a3_8pa_sportback
        model_full = model_dir.replace("_", " ")

        return selectedcategoryid, brandcar, model_full

    except Exception as e:
        logger.warning(f"Невозможно извлечь информацию из пути: {file_path}, ошибка: {e}")
        return None, None, None

def insert_product(conn, product_data, file_path):
    """Вставка основных данных о товаре"""
    cursor = conn.cursor()

    # Извлечение информации о марке и модели автомобиля
    selectedcategoryid, brandcar, model_full = extract_car_info_from_path(file_path)

    sql = """
    INSERT INTO products (
        id, title, active, available_quantity, price, price_with_delivery, 
        currency, delivery_price, delivery_period, url, seller_id, 
        seller_login, seller_rating, brandcar, model, selectedcategoryid
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE SET
        title = EXCLUDED.title,
        active = EXCLUDED.active,
        available_quantity = EXCLUDED.available_quantity,
        price = EXCLUDED.price,
        price_with_delivery = EXCLUDED.price_with_delivery,
        currency = EXCLUDED.currency,
        delivery_price = EXCLUDED.delivery_price,
        delivery_period = EXCLUDED.delivery_period,
        url = EXCLUDED.url,
        seller_id = EXCLUDED.seller_id,
        seller_login = EXCLUDED.seller_login,
        seller_rating = EXCLUDED.seller_rating,
        brandcar = EXCLUDED.brandcar,
        model = EXCLUDED.model,
        selectedcategoryid = EXCLUDED.selectedcategoryid,
        updated_at = CURRENT_TIMESTAMP
    RETURNING id
    """

    delivery_period = product_data.get("delivery_period")
    if delivery_period == "null" or delivery_period is None:
        delivery_period = None

    cursor.execute(
        sql,
        (
            product_data["id"],
            product_data["title"],
            product_data.get("active", True),
            product_data.get("availableQuantity", 0),
            product_data.get("price", 0),
            product_data.get("price_with_delivery", 0),
            product_data.get("currency", "PLN"),
            product_data.get("delivery_price", 0),
            delivery_period,
            product_data.get("url", ""),
            product_data.get("seller_id"),
            product_data.get("seller_login"),
            product_data.get("seller_rating"),
            brandcar,
            model_full,  # Исправлено: используем model_full вместо model
            selectedcategoryid,
        ),
    )

    product_id = cursor.fetchone()[0]
    cursor.close()
    return product_id

def insert_parameters(conn, product_id, specs_data):
    """Вставка параметров товара в отдельную таблицу"""
    if not specs_data or "Parametry" not in specs_data:
        return

    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_parameters WHERE product_id = %s", (product_id,))
    params = specs_data.get("Parametry", {})
    param_values = []

    for param_name, param_value in params.items():
        cursor.execute("SELECT id FROM parameter_types WHERE name = %s", (param_name,))
        result = cursor.fetchone()

        if result:
            param_type_id = result[0]
        else:
            cursor.execute(
                "INSERT INTO parameter_types (name) VALUES (%s) RETURNING id",
                (param_name,),
            )
            param_type_id = cursor.fetchone()[0]

        if isinstance(param_value, list):
            for value in param_value:
                param_values.append((product_id, param_type_id, value))
        else:
            param_values.append((product_id, param_type_id, param_value))

    if param_values:
        sql = """
        INSERT INTO product_parameters (product_id, parameter_id, value)
        VALUES (%s, %s, %s)
        ON CONFLICT (product_id, parameter_id, value) DO NOTHING
        """
        try:
            cursor.executemany(sql, param_values)
        except Exception as e:
            logger.warning(f"Ошибка при пакетной вставке параметров: {e}")
            for values in param_values:
                try:
                    cursor.execute(sql, values)
                except Exception as inner_e:
                    logger.error(f"Не удалось вставить параметр {values}: {inner_e}")

    cursor.close()

def insert_categories(conn, product_id, categories):
    """Вставка категорий и связей товара с категориями"""
    cursor = conn.cursor()

    for i, category in enumerate(categories):
        parent_id = None
        if i > 0:
            parent_id = categories[i - 1]["id"]

        sql = """
        INSERT INTO categories (id, name, url, parent_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            url = EXCLUDED.url
        """
        cursor.execute(
            sql, (category["id"], category["name"], category["url"], parent_id)
        )

        sql = """
        INSERT INTO product_categories (product_id, category_id)
        VALUES (%s, %s)
        ON CONFLICT (product_id, category_id) DO NOTHING
        """
        cursor.execute(sql, (product_id, category["id"]))

    cursor.close()

def insert_images(conn, product_id, images):
    """Вставка изображений товара"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM images WHERE product_id = %s", (product_id,))

    if images:
        records = [(product_id, img["original"], img.get("thumbnail"), img.get("embeded"), img.get("alt"), i) 
                   for i, img in enumerate(images)]
        sql = """
        INSERT INTO images (product_id, original_url, thumbnail_url, embedded_url, alt_text, position)
        VALUES %s
        """
        execute_values(cursor, sql, records)

    cursor.close()

def insert_specifications(conn, product_id, specifications):
    """Вставка характеристик товара с использованием JSONB"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM specifications WHERE product_id = %s", (product_id,))

    if specifications:
        for group_name, params in specifications.items():
            sql = """
            INSERT INTO specifications (product_id, param_group, parameters)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (product_id, group_name, json.dumps(params)))

    cursor.close()

def insert_description(conn, product_id, description):
    """Вставка описания товара"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM description_sections WHERE product_id = %s", (product_id,))

    if description and "sections" in description:
        for section_idx, section in enumerate(description["sections"]):
            cursor.execute(
                "INSERT INTO description_sections (product_id, position) VALUES (%s, %s) RETURNING id",
                (product_id, section_idx),
            )
            section_id = cursor.fetchone()[0]

            if "items" in section:
                records = [(section_id, item["type"], item.get("content"), item.get("url"), item.get("alt"), item_idx)
                           for item_idx, item in enumerate(section["items"])]
                sql = """
                INSERT INTO description_items (section_id, type, content, url, alt_text, position)
                VALUES %s
                """
                execute_values(cursor, sql, records)

    cursor.close()

def process_json_file(file_path):
    """Обработка одного JSON-файла и загрузка данных в БД"""
    file_path = Path(file_path)
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Проверяем, есть ли ключ products в данных
        products = data.get("products", [])
        if not products:
            logger.warning(f"Нет продуктов в файле: {file_path}")
            return

        conn = connect_to_db()
        try:
            with conn:
                for product_data in products:
                    product_id = insert_product(conn, product_data, file_path)
                    if "category_path" in product_data and product_data["category_path"]:
                        insert_categories(conn, product_id, product_data["category_path"])
                    if "images" in product_data and product_data["images"]:
                        insert_images(conn, product_id, product_data["images"])
                    if "specifications" in product_data and product_data["specifications"]:
                        insert_specifications(conn, product_id, product_data["specifications"])
                        insert_parameters(conn, product_id, product_data["specifications"])
                    if "description" in product_data and product_data["description"]:
                        insert_description(conn, product_id, product_data["description"])

            logger.info(f"Успешно обработан файл: {file_path}")

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Ошибка при обработке файла {file_path}: {e}")
        logger.exception("Трассировка ошибки:")

def process_directory(directory):
    """Обработка всех JSON-файлов в указанной директории и её поддиректориях"""
    directory_path = Path(directory)
    if not directory_path.is_dir():
        logger.error(f"Директория не существует: {directory}")
        return

    total_files = 0
    success_files = 0
    error_files = 0

    for json_file in directory_path.rglob("*.json"):
        total_files += 1
        try:
            process_json_file(json_file)
            success_files += 1
        except Exception as e:
            error_files += 1
            logger.error(f"Ошибка при обработке файла {json_file}: {e}")

    logger.info(f"Статистика обработки директории {directory}:")
    logger.info(f"Всего файлов: {total_files}")
    logger.info(f"Успешно обработано: {success_files}")
    logger.info(f"Ошибок: {error_files}")

if __name__ == "__main__":
    directory = "255099"
    process_directory(directory)