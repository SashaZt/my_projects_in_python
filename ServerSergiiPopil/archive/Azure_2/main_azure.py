import json
import pyodbc
import os
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("import_log.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def connect_to_db():
    """Установка соединения с базой данных Azure SQL"""
    try:
        conn = pyodbc.connect(
            "Driver={ODBC Driver 18 for SQL Server};"
            "Server=allegrosearchservice.database.windows.net,1433;"
            "Database=AlegroSearchService;"
            "UID=Igor;"
            "PWD=ZGIA_01078445iv;"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        return conn
    except pyodbc.Error as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise


def extract_car_info_from_path(file_path):
    """Извлечение информации о марке, модели и категории из пути к файлу"""
    # Получаем путь к папке с JSON-файлами (например, 'a8_d4')
    model_dir = os.path.basename(os.path.dirname(file_path))
    # Получаем путь к родительской папке (например, 'audi')
    brand_dir = os.path.basename(os.path.dirname(os.path.dirname(file_path)))
    # Получаем имя файла (например, '255099_01.json')
    file_name_json = os.path.basename(file_path)

    # Формируем brandcar и model_full
    brandcar = brand_dir.lower()  # Например, 'audi'
    model_full = model_dir.lower().replace("_", " ")  # Например, 'a8 d4'

    # Извлекаем category из имени файла (часть до первого '_')
    category = file_name_json.split("_")[0]  # Например, '255099'
    return brandcar, model_full, category


def insert_product(conn, product_data, file_path):
    """Вставка основных данных о товаре"""
    cursor = conn.cursor()

    # Извлечение информации о марке и модели автомобиля
    brandcar, model, selectedcategoryid = extract_car_info_from_path(file_path)

    # # Получение ID последней категории из category_path
    # selectedcategoryid = None
    # if "category_path" in product_data and product_data["category_path"]:
    #     selectedcategoryid = product_data["category_path"][-1]["id"]

    # SQL-запрос с использованием MERGE для upsert
    sql = """
    MERGE INTO parts_products AS target
    USING (SELECT 
        ? AS id, 
        ? AS title, 
        ? AS active, 
        ? AS available_quantity, 
        ? AS price, 
        ? AS price_with_delivery, 
        ? AS currency, 
        ? AS delivery_price, 
        ? AS delivery_period, 
        ? AS url, 
        ? AS seller_id, 
        ? AS seller_login, 
        ? AS seller_rating, 
        ? AS brandcar, 
        ? AS model, 
        ? AS selectedcategoryid) AS source
    ON target.id = source.id
    WHEN MATCHED THEN
        UPDATE SET
            title = source.title,
            active = source.active,
            available_quantity = source.available_quantity,
            price = source.price,
            price_with_delivery = source.price_with_delivery,
            currency = source.currency,
            delivery_price = source.delivery_price,
            delivery_period = source.delivery_period,
            url = source.url,
            seller_id = source.seller_id,
            seller_login = source.seller_login,
            seller_rating = source.seller_rating,
            brandcar = source.brandcar,
            model = source.model,
            selectedcategoryid = source.selectedcategoryid,
            updated_at = GETDATE()
    WHEN NOT MATCHED THEN
        INSERT (
            id, title, active, available_quantity, price, price_with_delivery, 
            currency, delivery_price, delivery_period, url, seller_id, 
            seller_login, seller_rating, brandcar, model, selectedcategoryid
        )
        VALUES (
            source.id, source.title, source.active, source.available_quantity, 
            source.price, source.price_with_delivery, source.currency, 
            source.delivery_price, source.delivery_period, source.url, 
            source.seller_id, source.seller_login, source.seller_rating, 
            source.brandcar, source.model, source.selectedcategoryid
        )
    OUTPUT inserted.id;
    """

    delivery_period = product_data.get("delivery_period")
    if delivery_period == "null" or delivery_period is None:
        delivery_period = None

    try:
        cursor.execute(
            sql,
            (
                product_data.get("id"),
                product_data.get("title"),
                1 if product_data.get("active", True) else 0,  # BIT вместо BOOLEAN
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
                model,
                selectedcategoryid,
            ),
        )

        product_id = cursor.fetchone()[0]
        conn.commit()
        return product_id

    except pyodbc.Error as e:
        logger.error(f"Ошибка при вставке продукта: {e}")
        raise
    finally:
        cursor.close()


def insert_parameters(conn, product_id, specs_data):
    """Вставка параметров товара в отдельную таблицу"""
    if not specs_data or "Parametry" not in specs_data:
        return

    cursor = conn.cursor()

    # Удаляем старые параметры
    cursor.execute(
        "DELETE FROM parts_product_parameters WHERE product_id = ?", (product_id,)
    )

    params = specs_data.get("Parametry", {})
    param_values = []

    for param_name, param_value in params.items():
        # Проверяем, существует ли тип параметра
        cursor.execute(
            "SELECT id FROM parts_parameter_types WHERE name = ?", (param_name,)
        )
        result = cursor.fetchone()

        if result:
            param_type_id = result[0]
        else:
            # Создаём новый тип параметра
            cursor.execute(
                "INSERT INTO parts_parameter_types (name) OUTPUT inserted.id VALUES (?)",
                (param_name,),
            )
            param_type_id = cursor.fetchone()[0]

        # Если значение — список, сохраняем каждое отдельно
        if isinstance(param_value, list):
            for value in param_value:
                if len(str(value)) <= 255:  # Учитываем ограничение NVARCHAR(255)
                    param_values.append((product_id, param_type_id, value))
                else:
                    logger.warning(
                        f"Значение параметра '{value}' для product_id={product_id} обрезано до 255 символов"
                    )
                    param_values.append((product_id, param_type_id, str(value)[:255]))
        else:
            if len(str(param_value)) <= 255:
                param_values.append((product_id, param_type_id, param_value))
            else:
                logger.warning(
                    f"Значение параметра '{param_value}' для product_id={product_id} обрезано до 255 символов"
                )
                param_values.append((product_id, param_type_id, str(param_value)[:255]))

    # Вставляем параметры
    if param_values:
        sql = """
        MERGE INTO parts_product_parameters AS target
        USING (SELECT ? AS product_id, ? AS parameter_id, ? AS value) AS source
        ON target.product_id = source.product_id 
           AND target.parameter_id = source.parameter_id 
           AND target.value = source.value
        WHEN NOT MATCHED THEN
            INSERT (product_id, parameter_id, value)
            VALUES (source.product_id, source.parameter_id, source.value);
        """

        try:
            for values in param_values:
                cursor.execute(sql, values)
            conn.commit()
        except pyodbc.Error as e:
            logger.error(f"Ошибка при вставке параметров: {e}")
            raise

    cursor.close()


def insert_categories(conn, product_id, categories):
    """Вставка категорий и связей товара с категориями"""
    cursor = conn.cursor()

    for i, category in enumerate(categories):
        parent_id = None
        if i > 0:
            parent_id = categories[i - 1]["id"]

        sql = """
        MERGE INTO parts_categories AS target
        USING (SELECT ? AS id, ? AS name, ? AS url, ? AS parent_id) AS source
        ON target.id = source.id
        WHEN MATCHED THEN
            UPDATE SET name = source.name, url = source.url
        WHEN NOT MATCHED THEN
            INSERT (id, name, url, parent_id)
            VALUES (source.id, source.name, source.url, source.parent_id);
        """
        cursor.execute(
            sql, (category["id"], category["name"], category["url"], parent_id)
        )

        # Связь с товаром
        sql = """
        MERGE INTO parts_product_categories AS target
        USING (SELECT ? AS product_id, ? AS category_id) AS source
        ON target.product_id = source.product_id AND target.category_id = source.category_id
        WHEN NOT MATCHED THEN
            INSERT (product_id, category_id)
            VALUES (source.product_id, source.category_id);
        """
        cursor.execute(sql, (product_id, category["id"]))

    conn.commit()
    cursor.close()


def insert_images(conn, product_id, images):
    """Вставка изображений товара"""
    cursor = conn.cursor()

    # Получаем информацию о колонке original_url для определения её максимальной длины
    cursor.execute(
        "SELECT CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'parts_images' AND COLUMN_NAME = 'original_url'"
    )
    max_length_result = cursor.fetchone()
    max_url_length = (
        max_length_result[0] if max_length_result else 255
    )  # По умолчанию 255, если не удалось получить

    cursor.execute("DELETE FROM parts_images WHERE product_id = ?", (product_id,))

    if images:
        records = []
        for i, image in enumerate(images):
            original_url = image["original"]
            thumbnail_url = image.get("thumbnail")
            embedded_url = image.get("embeded")
            alt_text = image.get("alt")

            # Проверка и обрезка URL, если они слишком длинные
            if original_url and len(original_url) > max_url_length:
                logger.warning(
                    f"URL изображения слишком длинный и будет обрезан: {original_url}"
                )
                original_url = original_url[:max_url_length]

            # Аналогичные проверки для thumbnail_url и embedded_url
            max_thumbnail_length = 255  # Укажите правильный размер
            max_embedded_length = 255  # Укажите правильный размер
            max_alt_length = 255  # Укажите правильный размер

            if thumbnail_url and len(thumbnail_url) > max_thumbnail_length:
                thumbnail_url = thumbnail_url[:max_thumbnail_length]

            if embedded_url and len(embedded_url) > max_embedded_length:
                embedded_url = embedded_url[:max_embedded_length]

            if alt_text and len(alt_text) > max_alt_length:
                alt_text = alt_text[:max_alt_length]

            records.append(
                (
                    product_id,
                    original_url,
                    thumbnail_url,
                    embedded_url,
                    alt_text,
                    i,
                )
            )

        sql = """
        INSERT INTO parts_images (product_id, original_url, thumbnail_url, embedded_url, alt_text, position)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            cursor.executemany(sql, records)
            conn.commit()
        except pyodbc.Error as e:
            conn.rollback()
            logger.error(f"Ошибка при вставке изображений: {e}")
            # Подробная отладка для понимания, какие данные вызывают проблему
            if records:
                for i, record in enumerate(records):
                    logger.debug(f"Запись {i}: {record}")
            raise

    cursor.close()


def insert_specifications(conn, product_id, specifications):
    """Вставка характеристик товара"""
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM parts_specifications WHERE product_id = ?", (product_id,)
    )

    if specifications:
        for group_name, params in specifications.items():
            # Пропускаем не-объекты и не-массивы
            if not isinstance(params, (dict, list)):
                # Если значение - булево, преобразуем его в объект
                if isinstance(params, bool):
                    params = {"value": params}
                else:
                    logger.info(
                        f"Пропущена группа '{group_name}' для product_id={product_id}, так как params не является объектом или массивом: {params}"
                    )
                    continue

            try:
                params_json = json.dumps(params, ensure_ascii=False)

                # Дополнительная проверка валидности JSON для SQL Server
                if not params_json.startswith(("{", "[")):
                    logger.error(
                        f"Невалидный JSON для product_id={product_id}, group={group_name}: {params_json}"
                    )
                    continue

                if len(params_json) > 4000:
                    logger.warning(
                        f"JSON спецификаций для product_id={product_id}, group={group_name} обрезан"
                    )
                    params_json = params_json[:4000]

                # Проверка на валидность JSON перед вставкой
                try:
                    # Повторный парсинг для проверки
                    json.loads(params_json)

                    sql = """
                    INSERT INTO parts_specifications (product_id, param_group, parameters)
                    VALUES (?, ?, ?)
                    """
                    cursor.execute(sql, (product_id, group_name, params_json))
                except json.JSONDecodeError as je:
                    logger.error(
                        f"Невалидный JSON после обработки для product_id={product_id}, group={group_name}: {je}"
                    )
                    continue

            except (ValueError, TypeError) as e:
                logger.error(
                    f"Ошибка сериализации JSON для product_id={product_id}, group={group_name}: {params}. Ошибка: {e}"
                )
                continue
            except pyodbc.Error as e:
                logger.error(
                    f"Ошибка вставки для product_id={product_id}, group={group_name}: {params_json}. Ошибка: {e}"
                )
                # Вывод дополнительной информации для отладки
                logger.error(f"Тип params: {type(params)}, Значение: {params}")
                continue

    conn.commit()
    cursor.close()


def insert_description(conn, product_id, description):
    """Вставка описания товара"""
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM parts_description_sections WHERE product_id = ?", (product_id,)
    )

    if description and "sections" in description:
        for section_idx, section in enumerate(description["sections"]):
            # Вставляем секцию
            cursor.execute(
                "INSERT INTO parts_description_sections (product_id, position) VALUES (?, ?)",
                (product_id, section_idx),
            )
            # Получаем ID последней вставленной записи
            cursor.execute("SELECT SCOPE_IDENTITY() AS id")
            section_id = cursor.fetchone()[0]

            if "items" in section:
                records = []
                for item_idx, item in enumerate(section["items"]):
                    records.append(
                        (
                            section_id,
                            item["type"],
                            item.get("content"),
                            item.get("url"),
                            item.get("alt"),
                            item_idx,
                        )
                    )

                sql = """
                INSERT INTO parts_description_items (section_id, type, content, url, alt_text, position)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.executemany(sql, records)

    conn.commit()
    cursor.close()


def process_json_file(file_path):
    """Обработка JSON-файла и загрузка данных в БД"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            datas = json.load(f)

        conn = connect_to_db()
        try:
            for data in datas["products"]:
                product_id = insert_product(conn, data, file_path)

                if "category_path" in data and data["category_path"]:
                    insert_categories(conn, product_id, data["category_path"])

                if "images" in data and data["images"]:
                    insert_images(conn, product_id, data["images"])

                if "specifications" in data and data["specifications"]:
                    insert_specifications(conn, product_id, data["specifications"])
                    insert_parameters(conn, product_id, data["specifications"])

                if "description" in data and data["description"]:
                    insert_description(conn, product_id, data["description"])

                logger.info(f"Успешно обработан товар: {data['id']}")

        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка при обработке файла {file_path}: {e}")
            logger.exception("Трассировка ошибки:")
            raise
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Ошибка при обработке файла {file_path}: {e}")
        logger.exception("Трассировка ошибки:")


def process_directory(directory_path):
    """Обработка всех JSON-файлов в директории"""
    total_files = 0
    success_files = 0
    error_files = 0

    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            total_files += 1
            file_path = os.path.join(directory_path, filename)

            try:
                process_json_file(file_path)
                success_files += 1  # Исправлено: убраны китайские иероглифы
            except Exception as e:
                error_files += 1
                logger.error(f"Ошибка при обработке файла {file_path}: {e}")

    logger.info(f"Статистика обработки директории {directory_path}:")
    logger.info(f"Всего файлов: {total_files}")
    logger.info(f"Успешно обработано: {success_files}")
    logger.info(f"Ошибок: {error_files}")


def process_car_directories(base_path):
    """Обработка всех директорий с моделями автомобилей"""
    total_dirs = 0
    processed_dirs = 0

    for dir_name in os.listdir(base_path):
        car_dir_path = os.path.join(base_path, dir_name)
        if os.path.isdir(car_dir_path):
            total_dirs += 1
            logger.info(f"Обработка директории модели: {dir_name}")

            try:
                process_directory(car_dir_path)
                processed_dirs += 1
            except Exception as e:
                logger.error(f"Ошибка при обработке директории {dir_name}: {e}")

    logger.info(f"Всего обработано {processed_dirs} директорий из {total_dirs}")


if __name__ == "__main__":
    file_name = "audi/a8_d4/255099_08.json"
    process_json_file(file_name)
