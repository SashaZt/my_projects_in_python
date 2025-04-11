# import json
# import psycopg2
# from psycopg2.extras import execute_values
# import os
# from logger import logger

# def connect_to_db():
#     """Установка соединения с базой данных"""
#     conn = psycopg2.connect(
#         host="10.0.0.18",
#         port="5430",
#         database="auto_parts_database",
#         user="auto_parts_database_user",
#         password="auto_parts_database_password"
#     )
#     return conn

# def extract_car_info_from_path(file_path):
#     """Извлечение информации о марке и модели автомобиля из пути к файлу"""
#     # Предполагается, что структура пути: /some/path/Audi-A8_D4/file.json
#     dir_name = os.path.basename(os.path.dirname(file_path))
    
#     # Парсинг имени директории для получения марки и модели
#     if '-' in dir_name and '_' in dir_name:
#         brand_model = dir_name.split('-')
#         brand = brand_model[0]
#         model_version = brand_model[1].split('_')
#         model = model_version[0]
#         version = model_version[1] if len(model_version) > 1 else ""
        
#         # Формирование brandcar и model
#         brandcar = f"{brand}-{model}"
#         model_full = version
        
#         return brandcar, model_full
    
#     # Если формат директории не соответствует ожидаемому
#     logger.warning(f"Невозможно извлечь информацию о марке и модели из пути: {file_path}")
#     return None, None

# def insert_product(conn, product_data, file_path):
#     """Вставка основных данных о товаре"""
#     cursor = conn.cursor()
    
#     # Извлечение информации о марке и модели автомобиля
#     brandcar, model = extract_car_info_from_path(file_path)
    
#     # Получение ID последней категории из category_path
#     selectedcategoryid = None
#     if 'category_path' in product_data and product_data['category_path']:
#         # Берем последний элемент из списка категорий
#         selectedcategoryid = product_data['category_path'][-1]['id']
    
#     # Вставка основной информации о товаре
#     sql = """
#     INSERT INTO products (
#         id, title, active, available_quantity, price, price_with_delivery, 
#         currency, delivery_price, delivery_period, url, seller_id, 
#         seller_login, seller_rating, brandcar, model, selectedcategoryid
#     ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#     ON CONFLICT (id) DO UPDATE SET
#         title = EXCLUDED.title,
#         active = EXCLUDED.active,
#         available_quantity = EXCLUDED.available_quantity,
#         price = EXCLUDED.price,
#         price_with_delivery = EXCLUDED.price_with_delivery,
#         currency = EXCLUDED.currency,
#         delivery_price = EXCLUDED.delivery_price,
#         delivery_period = EXCLUDED.delivery_period,
#         url = EXCLUDED.url,
#         seller_id = EXCLUDED.seller_id,
#         seller_login = EXCLUDED.seller_login,
#         seller_rating = EXCLUDED.seller_rating,
#         brandcar = EXCLUDED.brandcar,
#         model = EXCLUDED.model,
#         selectedcategoryid = EXCLUDED.selectedcategoryid,
#         updated_at = CURRENT_TIMESTAMP
#     RETURNING id
#     """
    
#     delivery_period = product_data.get('delivery_period')
#     # Если нужно преобразовать None в NULL
#     if delivery_period == 'null' or delivery_period is None:
#         delivery_period = None
    
#     cursor.execute(sql, (
#         product_data['id'],
#         product_data['title'],
#         product_data['active'],
#         product_data['availableQuantity'],
#         product_data['price'],
#         product_data['price_with_delivery'],
#         product_data['currency'],
#         product_data['delivery_price'],
#         delivery_period,
#         product_data['url'],
#         product_data['seller_id'],
#         product_data['seller_login'],
#         product_data['seller_rating'],
#         brandcar,
#         model,
#         selectedcategoryid
#     ))
    
#     product_id = cursor.fetchone()[0]
#     cursor.close()
#     return product_id

# def insert_categories(conn, product_id, categories):
#     """Вставка категорий и связей товара с категориями"""
#     cursor = conn.cursor()
    
#     # Вставка категорий (если не существуют)
#     for i, category in enumerate(categories):
#         # Определение parent_id на основе иерархии
#         parent_id = None
#         if i > 0:  # Если это не корневая категория
#             parent_id = categories[i-1]['id']
            
#         sql = """
#         INSERT INTO categories (id, name, url, parent_id)
#         VALUES (%s, %s, %s, %s)
#         ON CONFLICT (id) DO UPDATE SET
#             name = EXCLUDED.name,
#             url = EXCLUDED.url
#         """
        
#         cursor.execute(sql, (category['id'], category['name'], category['url'], parent_id))
        
#         # Связываем товар с категорией
#         sql = """
#         INSERT INTO product_categories (product_id, category_id)
#         VALUES (%s, %s)
#         ON CONFLICT (product_id, category_id) DO NOTHING
#         """
#         cursor.execute(sql, (product_id, category['id']))
    
#     cursor.close()

# def insert_images(conn, product_id, images):
#     """Вставка изображений товара"""
#     cursor = conn.cursor()
    
#     # Сначала удаляем старые изображения
#     cursor.execute("DELETE FROM images WHERE product_id = %s", (product_id,))
    
#     # Затем вставляем новые
#     if images:
#         records = []
#         for i, image in enumerate(images):
#             records.append((
#                 product_id,
#                 image['original'],
#                 image.get('thumbnail'),
#                 image.get('embeded'),
#                 image.get('alt'),
#                 i
#             ))
        
#         sql = """
#         INSERT INTO images (product_id, original_url, thumbnail_url, embedded_url, alt_text, position)
#         VALUES %s
#         """
#         execute_values(cursor, sql, records)
    
#     cursor.close()

# def insert_specifications(conn, product_id, specifications):
#     """Вставка характеристик товара с использованием JSONB"""
#     cursor = conn.cursor()
    
#     # Удаляем старые спецификации
#     cursor.execute("DELETE FROM specifications WHERE product_id = %s", (product_id,))
    
#     # Вставляем новые
#     if specifications:
#         for group_name, params in specifications.items():
#             sql = """
#             INSERT INTO specifications (product_id, param_group, params)
#             VALUES (%s, %s, %s)
#             """
#             cursor.execute(sql, (product_id, group_name, json.dumps(params)))
    
#     cursor.close()

# def insert_description(conn, product_id, description):
#     """Вставка описания товара"""
#     cursor = conn.cursor()
    
#     # Удаляем старые секции описания и их элементы (каскадно)
#     cursor.execute("DELETE FROM description_sections WHERE product_id = %s", (product_id,))
    
#     # Вставляем новые секции и их элементы
#     if description and 'sections' in description:
#         for section_idx, section in enumerate(description['sections']):
#             # Вставляем секцию
#             cursor.execute(
#                 "INSERT INTO description_sections (product_id, position) VALUES (%s, %s) RETURNING id",
#                 (product_id, section_idx)
#             )
#             section_id = cursor.fetchone()[0]
            
#             # Вставляем элементы секции
#             if 'items' in section:
#                 records = []
#                 for item_idx, item in enumerate(section['items']):
#                     records.append((
#                         section_id,
#                         item['type'],
#                         item.get('content'),
#                         item.get('url'),
#                         item.get('alt'),
#                         item_idx
#                     ))
                
#                 sql = """
#                 INSERT INTO description_items (section_id, type, content, url, alt_text, position)
#                 VALUES %s
#                 """
#                 execute_values(cursor, sql, records)
    
#     cursor.close()

# def process_json_file(file_path):
#     """Обработка JSON-файла и загрузка данных в БД"""
#     try:
#         with open(file_path, 'r', encoding='utf-8') as f:
#             data = json.load(f)
        
#         conn = connect_to_db()
#         try:
#             # Начинаем транзакцию
#             with conn:
#                 # Вставка основных данных о товаре с учетом пути к файлу
#                 product_id = insert_product(conn, data, file_path)
                
#                 # Вставка категорий
#                 if 'category_path' in data and data['category_path']:
#                     insert_categories(conn, product_id, data['category_path'])
                
#                 # Вставка изображений
#                 if 'images' in data and data['images']:
#                     insert_images(conn, product_id, data['images'])
                
#                 # Вставка спецификаций
#                 if 'specifications' in data and data['specifications']:
#                     insert_specifications(conn, product_id, data['specifications'])
                
#                 # Вставка описания
#                 if 'description' in data and data['description']:
#                     insert_description(conn, product_id, data['description'])
            
#             logger.info(f"Успешно обработан файл: {file_path}")
            
#         finally:
#             conn.close()
            
#     except Exception as e:
#         logger.error(f"Ошибка при обработке файла {file_path}: {e}")

# def process_directory(directory_path):
#     """Обработка всех JSON-файлов в директории"""
#     for filename in os.listdir(directory_path):
#         if filename.endswith('.json'):
#             file_path = os.path.join(directory_path, filename)
#             process_json_file(file_path)

# def process_car_directories(base_path):
#     """Обработка всех директорий с моделями автомобилей"""
#     for dir_name in os.listdir(base_path):
#         car_dir_path = os.path.join(base_path, dir_name)
#         if os.path.isdir(car_dir_path):
#             logger.info(f"Обработка директории модели: {dir_name}")
#             process_directory(car_dir_path)

# if __name__ == "__main__":
#     # Для обработки одной модели автомобиля
#     # process_directory('/path/to/Audi-A8_D4')
    
#     # Для обработки всех моделей автомобилей
#     # process_car_directories('/path/to/cars')
    
#     # Для теста можно использовать один файл
#     process_json_file('Audi-A8_D4/17321791696.json')


import json
import psycopg2
from psycopg2.extras import execute_values
import os
from logger import logger

def connect_to_db():
    """Установка соединения с базой данных"""
    conn = psycopg2.connect(
        host="10.0.0.18",
        port="5430",
        database="auto_parts_database",
        user="auto_parts_database_user",
        password="auto_parts_database_password"
    )
    return conn

def extract_car_info_from_path(file_path):
    """Извлечение информации о марке и модели автомобиля из пути к файлу"""
    # Предполагается, что структура пути: /some/path/Audi-A8_D4/file.json
    dir_name = os.path.basename(os.path.dirname(file_path))
    
    # Парсинг имени директории для получения марки и модели
    if '-' in dir_name and '_' in dir_name:
        brand_model = dir_name.split('-')
        brand = brand_model[0]
        model_version = brand_model[1].split('_')
        model = model_version[0]
        version = model_version[1] if len(model_version) > 1 else ""
        
        # Формирование brandcar и model
        brandcar = f"{brand}-{model}"
        model_full = version
        
        return brandcar, model_full
    
    # Если формат директории не соответствует ожидаемому
    logger.warning(f"Невозможно извлечь информацию о марке и модели из пути: {file_path}")
    return None, None

def insert_product(conn, product_data, file_path):
    """Вставка основных данных о товаре"""
    cursor = conn.cursor()
    
    # Извлечение информации о марке и модели автомобиля
    brandcar, model = extract_car_info_from_path(file_path)
    
    # Получение ID последней категории из category_path
    selectedcategoryid = None
    if 'category_path' in product_data and product_data['category_path']:
        # Берем последний элемент из списка категорий
        selectedcategoryid = product_data['category_path'][-1]['id']
    
    # Вставка основной информации о товаре
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
    
    delivery_period = product_data.get('delivery_period')
    # Если нужно преобразовать None в NULL
    if delivery_period == 'null' or delivery_period is None:
        delivery_period = None
    
    cursor.execute(sql, (
        product_data['id'],
        product_data['title'],
        product_data.get('active', True),
        product_data.get('availableQuantity', 0),
        product_data.get('price', 0),
        product_data.get('price_with_delivery', 0),
        product_data.get('currency', 'PLN'),
        product_data.get('delivery_price', 0),
        delivery_period,
        product_data.get('url', ''),
        product_data.get('seller_id'),
        product_data.get('seller_login'),
        product_data.get('seller_rating'),
        brandcar,
        model,
        selectedcategoryid
    ))
    
    product_id = cursor.fetchone()[0]
    cursor.close()
    return product_id

def insert_parameters(conn, product_id, specs_data):
    """Вставка параметров товара в отдельную таблицу"""
    if not specs_data or 'Parametry' not in specs_data:
        return
    
    cursor = conn.cursor()
    
    # Удаляем старые параметры для данного товара
    cursor.execute("DELETE FROM product_parameters WHERE product_id = %s", (product_id,))
    
    # Параметры из JSON
    params = specs_data.get('Parametry', {})
    
    # Подготовка значений для вставки
    param_values = []
    
    for param_name, param_value in params.items():
        # Проверяем, существует ли тип параметра
        cursor.execute(
            "SELECT id FROM parameter_types WHERE name = %s",
            (param_name,)
        )
        result = cursor.fetchone()
        
        if result:
            param_type_id = result[0]
        else:
            # Если типа параметра нет, создаем его
            cursor.execute(
                "INSERT INTO parameter_types (name) VALUES (%s) RETURNING id",
                (param_name,)
            )
            param_type_id = cursor.fetchone()[0]
        
        # Если значение параметра - список, сохраняем каждое значение отдельно
        if isinstance(param_value, list):
            for value in param_value:
                param_values.append((product_id, param_type_id, value))
        else:
            param_values.append((product_id, param_type_id, param_value))
    
    # Вставляем все параметры
    if param_values:
        sql = """
        INSERT INTO product_parameters (product_id, parameter_id, value)
        VALUES (%s, %s, %s)
        ON CONFLICT (product_id, parameter_id, value) DO NOTHING
        """
        
        try:
            cursor.executemany(sql, param_values)
        except Exception as e:
            # В случае ошибки попробуем вставить записи по одной
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
    
    # Вставка категорий (если не существуют)
    for i, category in enumerate(categories):
        # Определение parent_id на основе иерархии
        parent_id = None
        if i > 0:  # Если это не корневая категория
            parent_id = categories[i-1]['id']
            
        sql = """
        INSERT INTO categories (id, name, url, parent_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            url = EXCLUDED.url
        """
        
        cursor.execute(sql, (category['id'], category['name'], category['url'], parent_id))
        
        # Связываем товар с категорией
        sql = """
        INSERT INTO product_categories (product_id, category_id)
        VALUES (%s, %s)
        ON CONFLICT (product_id, category_id) DO NOTHING
        """
        cursor.execute(sql, (product_id, category['id']))
    
    cursor.close()

def insert_images(conn, product_id, images):
    """Вставка изображений товара"""
    cursor = conn.cursor()
    
    # Сначала удаляем старые изображения
    cursor.execute("DELETE FROM images WHERE product_id = %s", (product_id,))
    
    # Затем вставляем новые
    if images:
        records = []
        for i, image in enumerate(images):
            records.append((
                product_id,
                image['original'],
                image.get('thumbnail'),
                image.get('embeded'),
                image.get('alt'),
                i
            ))
        
        sql = """
        INSERT INTO images (product_id, original_url, thumbnail_url, embedded_url, alt_text, position)
        VALUES %s
        """
        execute_values(cursor, sql, records)
    
    cursor.close()

def insert_specifications(conn, product_id, specifications):
    """Вставка характеристик товара с использованием JSONB"""
    cursor = conn.cursor()
    
    # Удаляем старые спецификации
    cursor.execute("DELETE FROM specifications WHERE product_id = %s", (product_id,))
    
    # Вставляем новые
    if specifications:
        for group_name, params in specifications.items():
            sql = """
            INSERT INTO specifications (product_id, param_group, params)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (product_id, group_name, json.dumps(params)))
    
    cursor.close()

def insert_description(conn, product_id, description):
    """Вставка описания товара"""
    cursor = conn.cursor()
    
    # Удаляем старые секции описания и их элементы (каскадно)
    cursor.execute("DELETE FROM description_sections WHERE product_id = %s", (product_id,))
    
    # Вставляем новые секции и их элементы
    if description and 'sections' in description:
        for section_idx, section in enumerate(description['sections']):
            # Вставляем секцию
            cursor.execute(
                "INSERT INTO description_sections (product_id, position) VALUES (%s, %s) RETURNING id",
                (product_id, section_idx)
            )
            section_id = cursor.fetchone()[0]
            
            # Вставляем элементы секции
            if 'items' in section:
                records = []
                for item_idx, item in enumerate(section['items']):
                    records.append((
                        section_id,
                        item['type'],
                        item.get('content'),
                        item.get('url'),
                        item.get('alt'),
                        item_idx
                    ))
                
                sql = """
                INSERT INTO description_items (section_id, type, content, url, alt_text, position)
                VALUES %s
                """
                execute_values(cursor, sql, records)
    
    cursor.close()

def process_json_file(file_path):
    """Обработка JSON-файла и загрузка данных в БД"""
    print(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conn = connect_to_db()
        try:
            # Начинаем транзакцию
            with conn:
                # Вставка основных данных о товаре с учетом пути к файлу
                product_id = insert_product(conn, data, file_path)
                
                # Вставка категорий
                if 'category_path' in data and data['category_path']:
                    insert_categories(conn, product_id, data['category_path'])
                
                # Вставка изображений
                if 'images' in data and data['images']:
                    insert_images(conn, product_id, data['images'])
                
                # Вставка спецификаций как JSONB
                if 'specifications' in data and data['specifications']:
                    insert_specifications(conn, product_id, data['specifications'])
                    
                    # Вставка параметров в отдельную таблицу
                    insert_parameters(conn, product_id, data['specifications'])
                
                # Вставка описания
                if 'description' in data and data['description']:
                    insert_description(conn, product_id, data['description'])
            
            logger.info(f"Успешно обработан файл: {file_path}")
            
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
        if filename.endswith('.json'):
            total_files += 1
            file_path = os.path.join(directory_path, filename)
            
            try:
                process_json_file(file_path)
                success_files += 1
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
    # Настройка логирования
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("import_log.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Для обработки одной модели автомобиля
    # process_directory('/path/to/Audi-A8_D4')
    
    # Для обработки всех моделей автомобилей
    # process_car_directories('/path/to/cars')
    
    # Для теста можно использовать один файл
    file_name = 'Audi-A8_D4/17395362248.json'
    process_json_file(file_name)