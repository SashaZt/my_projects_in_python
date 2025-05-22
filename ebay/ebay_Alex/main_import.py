import json
from typing import Any, Dict, List

import psycopg2
from logger import logger
from psycopg2.extras import execute_values

# Конфигурация подключения к БД
db_config = {
    "host": "localhost",
    "database": "ebay",
    "user": "ebay_user",
    "password": "Pqm36q1kmcAlsVMIp2glEdfwNnj69X",
    "port": 5432,
}


def connect_to_db():
    """Создает подключение к базе данных"""
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        raise


def insert_product(cursor, product_data: Dict[str, Any]) -> bool:
    """Вставляет основную информацию о продукте"""
    try:
        insert_query = """
        INSERT INTO products (
            product_id, filename, title, category, url, price, returns, 
            shipping, delivery, condition_status, vehicle_vin, model, 
            model2, brand
        ) VALUES (
            %(product_id)s, %(filename)s, %(title)s, %(category)s, %(url)s, 
            %(price)s, %(returns)s, %(shipping)s, %(delivery)s, %(condition)s, 
            %(vehicle_vin)s, %(model)s, %(model2)s, %(brand)s
        ) ON CONFLICT (product_id) DO UPDATE SET
            filename = EXCLUDED.filename,
            title = EXCLUDED.title,
            category = EXCLUDED.category,
            url = EXCLUDED.url,
            price = EXCLUDED.price,
            returns = EXCLUDED.returns,
            shipping = EXCLUDED.shipping,
            delivery = EXCLUDED.delivery,
            condition_status = EXCLUDED.condition_status,
            vehicle_vin = EXCLUDED.vehicle_vin,
            model = EXCLUDED.model,
            model2 = EXCLUDED.model2,
            brand = EXCLUDED.brand,
            updated_at = CURRENT_TIMESTAMP
        """

        # Подготавливаем данные
        params = {
            "product_id": int(product_data.get("product_id", 0)),
            "filename": product_data.get("filename", ""),
            "title": product_data.get("title", ""),
            "category": product_data.get("category", ""),
            "url": product_data.get("url", ""),
            "price": (
                float(product_data.get("price", 0))
                if product_data.get("price")
                else None
            ),
            "returns": product_data.get("returns", ""),
            "shipping": product_data.get("shipping", ""),
            "delivery": product_data.get("delivery", ""),
            "condition": product_data.get("Condition", ""),
            "vehicle_vin": product_data.get("Vehicle VIN", ""),
            "model": product_data.get("Model", ""),
            "model2": product_data.get("Model2", ""),
            "brand": product_data.get("Brand", ""),
        }

        cursor.execute(insert_query, params)
        return True

    except Exception as e:
        logger.error(f"Ошибка вставки продукта {product_data.get('product_id')}: {e}")
        return False


def insert_product_images(
    cursor, product_id: int, product_data: Dict[str, Any]
) -> bool:
    """Вставляет изображения продукта"""
    try:
        # Удаляем существующие изображения
        cursor.execute(
            "DELETE FROM product_images WHERE product_id = %s", (product_id,)
        )

        # Подготавливаем данные изображений
        images_data = []
        for i in range(1, 4):
            url_key = f"url_image_{i}"
            local_key = f"image_{i}"

            image_url = product_data.get(url_key)
            local_path = product_data.get(local_key)

            # Добавляем только если есть хотя бы один из путей
            if image_url or local_path:
                images_data.append(
                    (
                        product_id,
                        image_url if image_url else None,
                        local_path if local_path else None,
                        i,
                    )
                )

        if images_data:
            insert_query = """
            INSERT INTO product_images (product_id, image_url, local_path, image_order)
            VALUES %s
            """
            execute_values(cursor, insert_query, images_data)

        return True

    except Exception as e:
        logger.error(f"Ошибка вставки изображений для продукта {product_id}: {e}")
        return False


def insert_part_numbers(cursor, product_id: int, product_data: Dict[str, Any]) -> bool:
    """Вставляет номера деталей"""
    try:
        # Удаляем существующие номера деталей
        cursor.execute(
            "DELETE FROM product_part_numbers WHERE product_id = %s", (product_id,)
        )

        # Подготавливаем данные номеров деталей
        part_numbers_data = []

        # Основные номера деталей
        if product_data.get("Manufacturer Part Number"):
            part_numbers_data.append(
                (
                    product_id,
                    "Manufacturer Part Number",
                    product_data["Manufacturer Part Number"],
                )
            )

        if product_data.get("Manufacturer Part Number2"):
            part_numbers_data.append(
                (
                    product_id,
                    "Manufacturer Part Number2",
                    product_data["Manufacturer Part Number2"],
                )
            )

        if part_numbers_data:
            insert_query = """
            INSERT INTO product_part_numbers (product_id, part_type, part_number)
            VALUES %s
            """
            execute_values(cursor, insert_query, part_numbers_data)

        return True

    except Exception as e:
        logger.error(f"Ошибка вставки номеров деталей для продукта {product_id}: {e}")
        return False


def insert_specifications(
    cursor, product_id: int, product_data: Dict[str, Any]
) -> bool:
    """Вставляет характеристики продукта"""
    try:
        # Удаляем существующие характеристики
        cursor.execute(
            "DELETE FROM product_specifications WHERE product_id = %s", (product_id,)
        )

        # Список всех характеристик из JSON
        specification_keys = [
            "Codice ricambio originale OE/OEM",
            "Condition and Options",
            "Conditions & Options",
            "Conditions and Options",
            "Direct Replacement",
            "Herstellernummer",
            "Interchange 1",
            "Interchange 2",
            "Interchange 3",
            "Interchange Part Number",
            "Material",
            "Mounting Style",
            "Numer części OE/OEM",
            "O.E. Part Number",
            "OE/OEM Part Number",
            "OE/OEM Referenznummer(n)",
            "OEM NO.",
            "Original Part Number OE/OEM",
            "POP_MPN",
            "POP_Other Part Number",
            "Referenznummer(n) OE",
            "Referenznummer(n) OEM",
            "Vergleichsnummer",
        ]

        # Подготавливаем данные характеристик
        specifications_data = []
        for spec_key in specification_keys:
            spec_value = product_data.get(spec_key)
            if spec_value:  # Добавляем только непустые значения
                specifications_data.append((product_id, spec_key, spec_value))

        if specifications_data:
            insert_query = """
            INSERT INTO product_specifications (product_id, spec_name, spec_value)
            VALUES %s
            """
            execute_values(cursor, insert_query, specifications_data)

        return True

    except Exception as e:
        logger.error(f"Ошибка вставки характеристик для продукта {product_id}: {e}")
        return False


def load_json_to_db(json_file_path: str) -> bool:
    """Основная функция загрузки JSON данных в БД"""
    try:
        # Читаем JSON файл
        with open(json_file_path, "r", encoding="utf-8") as f:
            products_data = json.load(f)

        logger.info(f"Загружено {len(products_data)} товаров из {json_file_path}")

        # Подключаемся к БД
        conn = connect_to_db()
        cursor = conn.cursor()

        success_count = 0
        error_count = 0

        try:
            for i, product_data in enumerate(products_data, 1):
                product_id = product_data.get("product_id")

                if not product_id:
                    logger.warning(f"Товар {i} не имеет product_id, пропускаем")
                    error_count += 1
                    continue

                try:
                    # Начинаем транзакцию для каждого товара
                    cursor.execute("BEGIN")

                    # Вставляем основную информацию о продукте
                    if not insert_product(cursor, product_data):
                        cursor.execute("ROLLBACK")
                        error_count += 1
                        continue

                    # Вставляем изображения
                    if not insert_product_images(cursor, int(product_id), product_data):
                        cursor.execute("ROLLBACK")
                        error_count += 1
                        continue

                    # Вставляем номера деталей
                    if not insert_part_numbers(cursor, int(product_id), product_data):
                        cursor.execute("ROLLBACK")
                        error_count += 1
                        continue

                    # Вставляем характеристики
                    if not insert_specifications(cursor, int(product_id), product_data):
                        cursor.execute("ROLLBACK")
                        error_count += 1
                        continue

                    # Подтверждаем транзакцию
                    cursor.execute("COMMIT")
                    success_count += 1

                    if i % 10 == 0:
                        logger.info(f"Обработано {i}/{len(products_data)} товаров")

                except Exception as e:
                    cursor.execute("ROLLBACK")
                    logger.error(f"Ошибка обработки товара {product_id}: {e}")
                    error_count += 1
                    continue

        finally:
            cursor.close()
            conn.close()

        logger.info(
            f"Загрузка завершена. Успешно: {success_count}, Ошибок: {error_count}"
        )
        return True

    except Exception as e:
        logger.error(f"Критическая ошибка загрузки в БД: {e}")
        return False


def verify_data_integrity():
    """Проверяет целостность загруженных данных"""
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        # Статистика по таблицам
        tables_stats = {}

        for table in [
            "products",
            "product_images",
            "product_part_numbers",
            "product_specifications",
        ]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            tables_stats[table] = count

        logger.info("Статистика по таблицам:")
        for table, count in tables_stats.items():
            logger.info(f"  {table}: {count} записей")

        # Проверяем товары без изображений
        cursor.execute(
            """
            SELECT COUNT(*) FROM products p 
            LEFT JOIN product_images pi ON p.product_id = pi.product_id 
            WHERE pi.product_id IS NULL
        """
        )
        products_without_images = cursor.fetchone()[0]
        logger.info(f"Товаров без изображений: {products_without_images}")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка проверки целостности данных: {e}")


if __name__ == "__main__":
    # Загружаем данные из JSON в БД
    if load_json_to_db("result.json"):
        logger.info("Данные успешно загружены в базу данных")

        # Проверяем целостность данных
        verify_data_integrity()
    else:
        logger.error("Ошибка загрузки данных в базу данных")
