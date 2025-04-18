import json
import psycopg2
from psycopg2.extras import execute_values, execute_batch
from pathlib import Path
from logger import logger
import concurrent.futures
import os
import time
import traceback


def connect_to_db():
    """Установка соединения с базой данных"""
    conn = psycopg2.connect(
        host="161.97.69.108",
        port="5430",
        database="auto_parts_database",
        user="auto_parts_database_user",
        password="auto_parts_database_password",
    )
    # Настраиваем автокоммит в False для явного управления транзакциями
    conn.autocommit = False
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
        logger.warning(
            f"Невозможно извлечь информацию из пути: {file_path}, ошибка: {e}"
        )
        return None, None, None


def simple_insert_approach(file_path):
    """Простой и надежный подход к вставке данных (без пакетной обработки)"""
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
        conn.autocommit = False  # Явно отключаем автокоммит

        try:
            cursor = conn.cursor()

            # Извлечение информации о марке и модели автомобиля из пути
            selectedcategoryid, brandcar, model_full = extract_car_info_from_path(
                file_path
            )

            # Кэш типов параметров
            param_types = {}
            cursor.execute("SELECT id, name FROM parameter_types")
            for param_id, param_name in cursor.fetchall():
                param_types[param_name] = param_id

            # Обрабатываем каждый продукт по одному
            for product in products:
                try:
                    # Вставка основной информации о продукте
                    delivery_period = product.get("delivery_period")
                    if delivery_period == "null" or delivery_period is None:
                        delivery_period = None

                    cursor.execute(
                        """
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
                    """,
                        (
                            product["id"],
                            product["title"],
                            product.get("active", True),
                            product.get("availableQuantity", 0),
                            product.get("price", 0),
                            product.get("price_with_delivery", 0),
                            product.get("currency", "PLN"),
                            product.get("delivery_price", 0),
                            delivery_period,
                            product.get("url", ""),
                            product.get("seller_id"),
                            product.get("seller_login"),
                            product.get("seller_rating"),
                            brandcar,
                            model_full,
                            selectedcategoryid,
                        ),
                    )

                    product_id = cursor.fetchone()[0]

                    # Вставка категорий
                    if "category_path" in product and product["category_path"]:
                        for i, category in enumerate(product["category_path"]):
                            parent_id = None
                            if i > 0:
                                parent_id = product["category_path"][i - 1]["id"]

                            cursor.execute(
                                """
                            INSERT INTO categories (id, name, url, parent_id)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                name = EXCLUDED.name,
                                url = EXCLUDED.url
                            """,
                                (
                                    category["id"],
                                    category["name"],
                                    category["url"],
                                    parent_id,
                                ),
                            )

                            cursor.execute(
                                """
                            INSERT INTO product_categories (product_id, category_id)
                            VALUES (%s, %s)
                            ON CONFLICT (product_id, category_id) DO NOTHING
                            """,
                                (product_id, category["id"]),
                            )

                    # Вставка изображений
                    if "images" in product and product["images"]:
                        cursor.execute(
                            "DELETE FROM images WHERE product_id = %s", (product_id,)
                        )

                        image_records = [
                            (
                                product_id,
                                img["original"],
                                img.get("thumbnail"),
                                img.get("embeded"),
                                img.get("alt"),
                                i,
                            )
                            for i, img in enumerate(product["images"])
                        ]

                        execute_values(
                            cursor,
                            """
                        INSERT INTO images (product_id, original_url, thumbnail_url, embedded_url, alt_text, position)
                        VALUES %s
                        """,
                            image_records,
                        )

                    # Вставка спецификаций
                    if "specifications" in product and product["specifications"]:
                        cursor.execute(
                            "DELETE FROM specifications WHERE product_id = %s",
                            (product_id,),
                        )

                        spec_records = [
                            (product_id, group_name, json.dumps(params))
                            for group_name, params in product["specifications"].items()
                        ]

                        execute_values(
                            cursor,
                            """
                        INSERT INTO specifications (product_id, param_group, parameters)
                        VALUES %s
                        """,
                            spec_records,
                        )

                        # Вставка параметров
                        if "Parametry" in product["specifications"]:
                            cursor.execute(
                                "DELETE FROM product_parameters WHERE product_id = %s",
                                (product_id,),
                            )

                            params = product["specifications"]["Parametry"]
                            param_records = []

                            for param_name, param_value in params.items():
                                # Проверяем или создаем тип параметра
                                if param_name not in param_types:
                                    cursor.execute(
                                        "INSERT INTO parameter_types (name) VALUES (%s) RETURNING id",
                                        (param_name,),
                                    )
                                    param_types[param_name] = cursor.fetchone()[0]

                                param_type_id = param_types[param_name]

                                # Собираем значения параметров
                                if isinstance(param_value, list):
                                    for value in param_value:
                                        param_records.append(
                                            (product_id, param_type_id, value)
                                        )
                                else:
                                    param_records.append(
                                        (product_id, param_type_id, param_value)
                                    )

                            # Вставляем параметры пакетом
                            if param_records:
                                execute_values(
                                    cursor,
                                    """
                                INSERT INTO product_parameters (product_id, parameter_id, value)
                                VALUES %s
                                ON CONFLICT (product_id, parameter_id, value) DO NOTHING
                                """,
                                    param_records,
                                )

                    # Вставка описания
                    if (
                        "description" in product
                        and product["description"]
                        and "sections" in product["description"]
                    ):
                        cursor.execute(
                            "DELETE FROM description_sections WHERE product_id = %s",
                            (product_id,),
                        )

                        for section_idx, section in enumerate(
                            product["description"]["sections"]
                        ):
                            cursor.execute(
                                "INSERT INTO description_sections (product_id, position) VALUES (%s, %s) RETURNING id",
                                (product_id, section_idx),
                            )
                            section_id = cursor.fetchone()[0]

                            if "items" in section:
                                item_records = [
                                    (
                                        section_id,
                                        item["type"],
                                        item.get("content"),
                                        item.get("url"),
                                        item.get("alt"),
                                        item_idx,
                                    )
                                    for item_idx, item in enumerate(section["items"])
                                ]

                                execute_values(
                                    cursor,
                                    """
                                INSERT INTO description_items (section_id, type, content, url, alt_text, position)
                                VALUES %s
                                """,
                                    item_records,
                                )

                    # Коммитим изменения для этого продукта
                    conn.commit()

                except Exception as product_error:
                    # Если произошла ошибка при обработке продукта, откатываем изменения только для этого продукта
                    conn.rollback()
                    logger.error(
                        f"Ошибка при обработке продукта {product.get('id')} в файле {file_path}: {product_error}"
                    )
                    # Продолжаем со следующим продуктом

            logger.info(f"Успешно обработан файл: {file_path}")

        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка при обработке файла {file_path}: {e}")
            raise
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Ошибка при открытии или парсинге файла {file_path}: {e}")
        logger.exception("Трассировка ошибки:")
        raise


def batch_process_files(file_paths, batch_size=5):
    """Обработка файлов небольшими порциями с одним соединением"""
    if not file_paths:
        return

    conn = connect_to_db()

    try:
        # Кэшируем типы параметров
        param_types = {}
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM parameter_types")
            for param_id, param_name in cursor.fetchall():
                param_types[param_name] = param_id

        # Обрабатываем файлы пакетами
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i : i + batch_size]
            logger.info(
                f"Обработка пакета файлов {i//batch_size + 1}/{(len(file_paths) + batch_size - 1)//batch_size}"
            )

            for file_path in batch:
                try:
                    # Для каждого файла используем отдельную транзакцию
                    simple_insert_approach(file_path)
                except Exception as e:
                    logger.error(
                        f"Ошибка при обработке файла в пакете: {file_path}: {e}"
                    )

    finally:
        conn.close()


def process_directory_sequential(directory):
    """Последовательная обработка JSON-файлов - простой и надежный подход"""
    directory_path = Path(directory)
    if not directory_path.is_dir():
        logger.error(f"Директория не существует: {directory}")
        return

    # Получаем список всех JSON-файлов
    json_files = list(directory_path.rglob("*.json"))
    total_files = len(json_files)

    if total_files == 0:
        logger.info(f"В директории {directory} не найдено JSON-файлов")
        return

    logger.info(f"Найдено {total_files} JSON-файлов для обработки")

    success_files = 0
    error_files = 0

    # Обрабатываем каждый файл последовательно
    for i, json_file in enumerate(json_files):
        logger.info(f"Обработка файла {i+1}/{total_files}: {json_file}")

        try:
            # Используем простой подход к вставке
            simple_insert_approach(json_file)
            success_files += 1
            logger.info(f"Успешно обработан файл {i+1}/{total_files}")
        except Exception as e:
            error_files += 1
            logger.error(f"Ошибка при обработке файла {json_file}: {e}")

    logger.info(f"Статистика обработки директории {directory}:")
    logger.info(f"Всего файлов: {total_files}")
    logger.info(f"Успешно обработано: {success_files}")
    logger.info(f"Ошибок: {error_files}")


def process_directory_parallel(directory, max_workers=4):
    """Параллельная обработка JSON-файлов с использованием нескольких потоков"""
    directory_path = Path(directory)
    if not directory_path.is_dir():
        logger.error(f"Директория не существует: {directory}")
        return

    # Получаем список всех JSON-файлов
    json_files = list(directory_path.rglob("*.json"))
    total_files = len(json_files)

    if total_files == 0:
        logger.info(f"В директории {directory} не найдено JSON-файлов")
        return

    logger.info(
        f"Найдено {total_files} JSON-файлов для параллельной обработки с {max_workers} потоками"
    )

    success_files = 0
    error_files = 0

    # Используем ThreadPoolExecutor для параллельной обработки
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Отправляем задачи на выполнение
        future_to_file = {
            executor.submit(simple_insert_approach, file): file for file in json_files
        }

        # Обрабатываем результаты по мере их поступления
        for i, future in enumerate(concurrent.futures.as_completed(future_to_file), 1):
            file = future_to_file[future]
            try:
                future.result()  # Получаем результат (или исключение)
                success_files += 1
                logger.info(f"Успешно обработан файл ({i}/{total_files}): {file}")
            except Exception as e:
                error_files += 1
                logger.error(f"Ошибка при обработке файла {file}: {e}")

    logger.info(f"Статистика обработки директории {directory}:")
    logger.info(f"Всего файлов: {total_files}")
    logger.info(f"Успешно обработано: {success_files}")
    logger.info(f"Ошибок: {error_files}")


if __name__ == "__main__":
    directory = "255099"

    # Выбор между последовательной и параллельной обработкой
    use_parallel = False  # Установите в True для параллельной обработки

    try:
        # Проверяем соединение с базой данных
        conn = connect_to_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone():
                logger.info("Соединение с базой данных успешно установлено")
            else:
                logger.error("Не удалось подключиться к базе данных")
                exit(1)
        conn.close()

        if use_parallel:
            # Параллельная обработка (может быть быстрее, но менее стабильна)
            max_workers = 4  # Ограничиваем до 4 потоков для большей стабильности
            logger.info(f"Запуск параллельной обработки с {max_workers} потоками")
            process_directory_parallel(directory, max_workers)
        else:
            # Последовательная обработка (медленнее, но более стабильна)
            logger.info("Запуск последовательной обработки")
            process_directory_sequential(directory)

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.exception("Трассировка ошибки:")
