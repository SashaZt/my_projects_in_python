import json
import re
from typing import Any, Dict, List, Optional

import psycopg2
from config.logger import logger
from psycopg2.extras import RealDictCursor, execute_values

# Конфигурация подключения к БД
DB_CONFIG = {
    "host": "localhost",
    "database": "klarstein_pl",
    "user": "klarstein_pl_user",
    "password": "Pqm36q1kmcAlsVMIp2glEdfwNnj69X",
    "port": 5431,
}


class KlarsteinProductLoader:
    """Класс для загрузки продуктов Klarstein в PostgreSQL (новая схема)"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection = None

    def connect_to_db(self):
        """Создает подключение к базе данных"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = False
            logger.info("Успешное подключение к базе данных")
            return self.connection
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise

    def close_connection(self):
        """Закрывает подключение к БД"""
        if self.connection:
            self.connection.close()
            logger.info("Подключение к БД закрыто")

    def extract_vendor_code_from_sku(self, sku: str) -> int:
        """Извлекает vendor_code из SKU"""
        # Убираем префикс Kla и извлекаем числовую часть
        sku_clean = sku.replace("Kla", "").replace("kla", "")
        match = re.search(r"(\d+)", sku_clean)
        if match:
            return int(match.group(1))
        else:
            # Если не найдено число, используем хеш от SKU
            return abs(hash(sku)) % (2**31)

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """
        Получает все категории из БД для построения дерева
        Возвращает список категорий с правильной структурой для XML
        """
        try:
            if not self.connect_to_db():
                return []

            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            query = """
            SELECT 
                category_id,
                parent_id,
                name_pl,
                name,
                name_ua,
                created_at
            FROM categories 
            ORDER BY 
                CASE WHEN parent_id IS NULL THEN 0 ELSE 1 END,  -- Сначала родительские
                parent_id NULLS FIRST,                          -- Потом по parent_id
                category_id                                     -- Потом по id
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                logger.warning("Категории не найдены в БД")
                return []

            categories = []
            for row in rows:
                category = {
                    "category_id": row["category_id"],  # Для XML: id
                    "parent_id": row["parent_id"],  # Для XML: parentId
                    "name_pl": row["name_pl"] or "",  # польское название
                    "name": row["name"] or "",  # русское название
                    "name_ua": row["name_ua"] or "",  # украинское название
                    "created_at": row["created_at"],
                }
                categories.append(category)

            logger.info(f"Загружено {len(categories)} категорий из БД")
            return categories

        except Exception as e:
            logger.error(f"Ошибка при загрузке категорий: {e}")
            return []
        finally:
            self.close_connection()

    def get_products_for_export(self) -> List[Dict[str, Any]]:
        """Получает товары с export_xml = false (НЕ выгруженные в XML)"""
        try:
            if not self.connect_to_db():
                return []

            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            # ИСПРАВЛЕННЫЙ SQL: добавлено поле quantity
            query = """
            SELECT 
                p.id, p.product_id, p.vendor_code, p.available, p.selling_type, 
                p.price, p.price_opt1,p.price_opt2, p.quantity1,p.quantity2,p.discount, p.currency_id, p.category_id, 
                p.name_pl, p.name, p.name_ua, p.vendor, p.country_of_origin,
                p.keywords_pl, p.keywords, p.keywords_ua,
                p.description_pl, p.description, p.description_ua,
                p.created_at, p.updated_at, p.export_xml,
                -- ИСПРАВЛЕНО: сортировка вынесена в подзапрос
                (
                    SELECT array_agg(pi2.image_url ORDER BY pi2.image_order)
                    FROM product_images pi2 
                    WHERE pi2.product_id = p.product_id
                ) as images,
                pd.width, pd.height, pd.length, pd.weight
            FROM products p
            LEFT JOIN product_dimensions pd ON p.product_id = pd.product_id
            WHERE p.export_xml = false  -- НЕ выгруженные товары
            ORDER BY p.created_at DESC
            """

            cursor.execute(query)
            results = cursor.fetchall()

            # Преобразуем результаты в список словарей
            products = []
            for row in results:
                product = dict(row)
                # Убираем None значения из массива изображений
                if product.get("images"):
                    product["images"] = [img for img in product["images"] if img]
                else:
                    product["images"] = []
                products.append(product)

            cursor.close()
            logger.info(f"Получено {len(products)} товаров для экспорта")
            return products

        except Exception as e:
            logger.error(f"Ошибка получения товаров для экспорта: {e}")
            return []
        finally:
            self.close_connection()

    def mark_as_exported(self, product_ids: List[str]) -> bool:
        """Помечает товары как выгруженные (export_xml = true)"""
        try:
            if not product_ids:
                logger.warning("Пустой список товаров для пометки как экспортированные")
                return False

            if not self.connect_to_db():
                return False

            cursor = self.connection.cursor()

            query = """
            UPDATE products 
            SET export_xml = true, updated_at = NOW()
            WHERE product_id = ANY(%s)
            """

            cursor.execute(query, (product_ids,))
            affected_rows = cursor.rowcount

            if affected_rows > 0:
                self.connection.commit()
                logger.info(f"Помечено как выгруженные {affected_rows} товаров")
                return True
            else:
                logger.warning("Не найдено товаров для обновления")
                return False

        except Exception as e:
            self.connection.rollback()
            logger.error(f"Ошибка пометки товаров как выгруженных: {e}")
            return False
        finally:
            self.close_connection()

    def load_data_to_db(self, data) -> bool:
        """Загружает данные напрямую в базу данных (принимает один YML объект)"""
        try:
            # Подключаемся к БД
            if not self.connect_to_db():
                return False

            cursor = self.connection.cursor()

            try:
                # Определяем тип структуры данных
                if isinstance(data, dict):
                    if "shop_info" in data and "offers" in data:
                        # Новая YML структура
                        success = self.process_yml_structure(cursor, data)
                    elif "product" in data:
                        # Старый формат с одним продуктом
                        success = self.process_single_product(cursor, data)
                    else:
                        logger.error("Неизвестная структура JSON")
                        return False
                elif isinstance(data, list):
                    # Массив продуктов (старый формат)
                    success_count = 0
                    for product_data in data:
                        if self.process_single_product(cursor, product_data):
                            success_count += 1
                    success = success_count > 0
                else:
                    logger.error("JSON должен быть объектом или массивом")
                    return False

                if success:
                    self.connection.commit()
                    logger.info("Данные успешно загружены в БД")
                else:
                    self.connection.rollback()
                    logger.error("Ошибка загрузки данных, откат изменений")

                return success

            except Exception as e:
                self.connection.rollback()
                logger.error(f"Критическая ошибка, откат транзакции: {e}")
                return False
            finally:
                cursor.close()

        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")
            return False
        finally:
            self.close_connection()

    def insert_categories(self, cursor, categories_data: List[Dict[str, Any]]) -> bool:
        """Вставляет категории в БД"""
        try:
            if not categories_data:
                return True

            for category in categories_data:
                category_id = category.get("id")
                parent_id = category.get("parentId")
                name_pl = category.get("name_pl", "")
                name = category.get("name", "")
                name_ua = category.get("name_ua", "")

                # Проверяем, существует ли категория
                cursor.execute(
                    "SELECT COUNT(*) FROM categories WHERE category_id = %s",
                    (category_id,),
                )
                exists = cursor.fetchone()[0] > 0

                if exists:
                    # Обновляем существующую категорию
                    update_query = """
                        UPDATE categories SET
                            parent_id = %s,
                            name_pl = %s,
                            name = %s,
                            name_ua = %s,
                            updated_at = NOW()
                        WHERE category_id = %s
                    """
                    cursor.execute(
                        update_query, (parent_id, name_pl, name, name_ua, category_id)
                    )
                    logger.info(f"Обновлена категория ID: {category_id}")
                else:
                    # Вставляем новую категорию
                    insert_query = """
                        INSERT INTO categories (category_id, parent_id, name_pl, name, name_ua)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(
                        insert_query, (category_id, parent_id, name_pl, name, name_ua)
                    )
                    logger.info(f"Добавлена категория ID: {category_id}")

            logger.info(f"Обработано {len(categories_data)} категорий")
            return True

        except Exception as e:
            logger.error(f"Ошибка при вставке категорий: {e}")
            return False

    def insert_product(self, cursor, offer_data: Dict[str, Any]) -> Optional[str]:
        """Вставляет основную информацию о продукте (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
        try:
            product_id = offer_data.get("id", "")
            if not product_id:
                logger.warning("product_id отсутствует в данных продукта")
                return None

            # Извлекаем vendor_code - сначала пробуем из данных, потом из product_id
            vendor_code = offer_data.get("vendorCode")
            if not vendor_code:
                vendor_code = self.extract_vendor_code_from_sku(product_id)

            # Конвертируем цену в число
            quantity1 = offer_data.get("quantity1")
            quantity2 = offer_data.get("quantity2")
            discount = offer_data.get("discount")

            price = offer_data.get("price")
            if price:
                try:
                    price = float(str(price).replace(",", "."))
                except (ValueError, TypeError):
                    price = 0.0
            price_opt1 = offer_data.get("price_opt1")
            logger.info(price_opt1)
            if price_opt1:
                try:
                    price_opt1 = float(str(price_opt1).replace(",", "."))
                except (ValueError, TypeError):
                    price_opt1 = 0.0
            price_opt2 = offer_data.get("price_opt2")
            logger.info(price_opt2)
            if price_opt2:
                try:
                    price_opt2 = float(str(price_opt2).replace(",", "."))
                except (ValueError, TypeError):
                    price_opt2 = 0.0

            # Проверяем, существует ли продукт
            cursor.execute(
                "SELECT COUNT(*) FROM products WHERE product_id = %s", (product_id,)
            )
            exists = cursor.fetchone()[0] > 0

            if exists:
                # Обновляем существующий продукт
                update_query = """
                    UPDATE products SET
                        vendor_code = %s,
                        available = %s,
                        selling_type = %s,
                        price = %s,
                        price_opt1 = %s,
                        price_opt2 = %s,
                        discount = %s,
                        quantity1 = %s,
                        quantity2 = %s,
                        currency_id = %s,
                        category_id = %s,
                        name_pl = %s,
                        name = %s,
                        name_ua = %s,
                        vendor = %s,
                        country_of_origin = %s,
                        keywords_pl = %s,
                        keywords = %s,
                        keywords_ua = %s,
                        description_pl = %s,
                        description = %s,
                        description_ua = %s,
                        updated_at = NOW()
                    WHERE product_id = %s
                    RETURNING product_id
                """
                cursor.execute(
                    update_query,
                    (
                        vendor_code,
                        offer_data.get("available", "true") == "true",
                        offer_data.get("selling_type", "u"),
                        price,
                        price_opt1,
                        price_opt2,
                        discount,
                        quantity1,
                        quantity2,
                        offer_data.get("currencyId", "UAH"),
                        int(offer_data.get("categoryId", 1)),
                        offer_data.get("name_pl", ""),
                        offer_data.get("name", ""),
                        offer_data.get("name_ua", ""),
                        offer_data.get("vendor", "Klarstein"),
                        offer_data.get("country_of_origin", "Германия"),
                        offer_data.get("keywords_pl", ""),
                        offer_data.get("keywords", ""),
                        offer_data.get("keywords_ua", ""),
                        offer_data.get("description_pl", ""),
                        offer_data.get("description", ""),
                        offer_data.get("description_ua", ""),
                        product_id,
                    ),
                )
                logger.info(
                    f"Обновлен продукт {product_id} (vendor_code: {vendor_code})"
                )
            else:
                # Вставляем новый продукт
                insert_query = """
                    INSERT INTO products (
                        product_id, vendor_code, available, selling_type, price,price_opt1,price_opt2,discount,quantity1,quantity2, currency_id,
                        category_id, name_pl, name, name_ua, vendor, country_of_origin,keywords_pl, keywords, keywords_ua,
                        description_pl, description, description_ua
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s
                    )
                    RETURNING product_id
                """
                cursor.execute(
                    insert_query,
                    (
                        product_id,
                        vendor_code,
                        offer_data.get("available", "true") == "true",
                        offer_data.get("selling_type", "u"),
                        price,
                        price_opt1,
                        price_opt2,
                        discount,
                        quantity1,
                        quantity2,
                        offer_data.get("currencyId", "UAH"),
                        int(offer_data.get("categoryId", 1)),
                        offer_data.get("name_pl", ""),
                        offer_data.get("name", ""),
                        offer_data.get("name_ua", ""),
                        offer_data.get("vendor", "Klarstein"),
                        offer_data.get("country_of_origin", "Германия"),
                        offer_data.get("keywords_pl", ""),
                        offer_data.get("keywords", ""),
                        offer_data.get("keywords_ua", ""),
                        offer_data.get("description_pl", ""),
                        offer_data.get("description", ""),
                        offer_data.get("description_ua", ""),
                    ),
                )
                logger.info(
                    f"Добавлен продукт {product_id} (vendor_code: {vendor_code})"
                )

            result = cursor.fetchone()
            return result[0] if result else product_id

        except Exception as e:
            logger.error(
                f"Ошибка при вставке продукта {offer_data.get('id', 'unknown')}: {e}"
            )
            return None

    def insert_product_images(self, cursor, product_id: str, images: List[str]) -> bool:
        """Вставляет изображения продукта"""
        try:
            # Удаляем существующие изображения
            cursor.execute(
                "DELETE FROM product_images WHERE product_id = %s", (product_id,)
            )

            if not images:
                return True

            # Подготавливаем данные (максимум 10 изображений)
            images_data = []
            for order, image_url in enumerate(images[:10], 1):
                if image_url and image_url.strip():
                    images_data.append((product_id, image_url.strip(), order))

            if images_data:
                insert_query = """
                    INSERT INTO product_images (product_id, image_url, image_order)
                    VALUES %s
                """
                execute_values(cursor, insert_query, images_data)
                logger.info(
                    f"Добавлено {len(images_data)} изображений для товара {product_id}"
                )

            return True

        except Exception as e:
            logger.error(
                f"Ошибка при вставке изображений для продукта {product_id}: {e}"
            )
            return False

    def insert_product_dimensions(
        self, cursor, product_id: str, dimensions: Dict[str, Any]
    ) -> bool:
        """Вставляет размеры продукта"""
        try:
            # Удаляем существующие размеры
            cursor.execute(
                "DELETE FROM product_dimensions WHERE product_id = %s", (product_id,)
            )

            if not dimensions:
                return True

            # Извлекаем размеры
            width = self._safe_float(dimensions.get("width"))
            height = self._safe_float(dimensions.get("height"))
            length = self._safe_float(dimensions.get("length"))
            weight = self._safe_float(dimensions.get("weight"))

            # Вставляем только если есть хотя бы один размер
            if any([width, height, length, weight]):
                insert_query = """
                    INSERT INTO product_dimensions (product_id, width, height, length, weight)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(
                    insert_query, (product_id, width, height, length, weight)
                )
                logger.info(f"Добавлены размеры для товара {product_id}")

            return True

        except Exception as e:
            logger.error(f"Ошибка при вставке размеров для продукта {product_id}: {e}")
            return False

    def _safe_float(self, value) -> float:
        """Безопасное преобразование в float с значением по умолчанию 0"""
        if value is None or value == "":
            return 0.0
        try:
            # Убираем пробелы и заменяем запятую на точку
            clean_value = str(value).strip().replace(",", ".")
            return float(clean_value)
        except (ValueError, TypeError):
            return 0.0

    def process_yml_structure(self, cursor, yml_data: Dict[str, Any]) -> bool:
        """Обрабатывает данные в YML структуре"""
        try:
            # 1. Вставляем категории
            categories = yml_data.get("categories", [])
            if not self.insert_categories(cursor, categories):
                return False

            # 2. Обрабатываем товары
            offers = yml_data.get("offers", [])
            if not offers:
                logger.warning("Нет товаров для обработки")
                return True

            success_count = 0
            for offer in offers:
                try:
                    # Начинаем savepoint для каждого товара
                    cursor.execute("SAVEPOINT offer_savepoint")

                    # Вставляем основную информацию о товаре
                    product_id = self.insert_product(cursor, offer)
                    if not product_id:
                        cursor.execute("ROLLBACK TO SAVEPOINT offer_savepoint")
                        continue

                    # Вставляем изображения
                    images = offer.get("pictures", [])
                    if not self.insert_product_images(cursor, product_id, images):
                        cursor.execute("ROLLBACK TO SAVEPOINT offer_savepoint")
                        continue

                    # Вставляем размеры
                    dimensions = offer.get("dimensions", {})
                    if not self.insert_product_dimensions(
                        cursor, product_id, dimensions
                    ):
                        cursor.execute("ROLLBACK TO SAVEPOINT offer_savepoint")
                        continue

                    cursor.execute("RELEASE SAVEPOINT offer_savepoint")
                    success_count += 1
                    logger.info(f"Товар {product_id} успешно обработан")

                except Exception as e:
                    cursor.execute("ROLLBACK TO SAVEPOINT offer_savepoint")
                    logger.error(f"Ошибка обработки товара: {e}")

            logger.info(f"Успешно обработано {success_count} из {len(offers)} товаров")
            return success_count > 0

        except Exception as e:
            logger.error(f"Ошибка обработки YML структуры: {e}")
            return False

    def process_single_product(self, cursor, product_data: Dict[str, Any]) -> bool:
        """Обрабатывает один продукт (старый формат)"""
        try:
            # Конвертируем старый формат в новый
            if "product" in product_data:
                product_info = product_data["product"]
                breadcrumbs = product_data.get("breadcrumbs_pl", [])
                descriptions = product_data.get("description_pl", [])

                # Создаем структуру категорий из breadcrumbs
                categories = []
                for idx, category_name in enumerate(breadcrumbs, 1):
                    categories.append(
                        {
                            "id": idx,
                            "name_pl": category_name,
                            "name": category_name,
                            "name_ua": category_name,
                            "parentId": idx - 1 if idx > 1 else None,
                        }
                    )

                # Создаем структуру offer
                offer = {
                    "id": product_info.get("sku", ""),
                    "available": "true",
                    "selling_type": "u",
                    "price": product_info.get("price", "0"),
                    "price_opt1": product_info.get("price_opt1", "0"),
                    "price_opt2": product_info.get("price_opt2", "0"),
                    "quantity1": product_info.get("quantity1", "0"),
                    "quantity2": product_info.get("quantity2", "0"),
                    "discount": product_info.get("discount", "0"),
                    "currencyId": "UAH",
                    "categoryId": str(len(categories)) if categories else "1",
                    "name_pl": product_info.get("name_pl", ""),
                    "name": "",
                    "name_ua": "",
                    "vendor": "Klarstein",
                    "country_of_origin": "Германия",
                    "pictures": product_info.get("images", []),
                    "description_pl": "",
                    "description": "",
                    "description_ua": "",
                    "dimensions": product_data.get("product_specifications", {}),
                }

                # Создаем YML структуру
                yml_structure = {"categories": categories, "offers": [offer]}

                return self.process_yml_structure(cursor, yml_structure)
            else:
                logger.error("Неподдерживаемый формат данных продукта")
                return False

        except Exception as e:
            logger.error(f"Ошибка обработки одного продукта: {e}")
            return False

    def load_json_file(self, data: dict) -> bool:
        """Загружает данные из JSON файла в базу данных"""
        try:
            cursor = self.connection.cursor()

            try:
                # Определяем тип структуры данных
                if isinstance(data, dict):
                    if "shop_info" in data and "offers" in data:
                        # Новая YML структура
                        success = self.process_yml_structure(cursor, data)
                    elif "product" in data:
                        # Старый формат с одним продуктом
                        success = self.process_single_product(cursor, data)
                    else:
                        logger.error("Неизвестная структура JSON")
                        return False
                elif isinstance(data, list):
                    # Массив продуктов (старый формат)
                    success_count = 0
                    for product_data in data:
                        if self.process_single_product(cursor, product_data):
                            success_count += 1
                    success = success_count > 0
                else:
                    logger.error("JSON должен быть объектом или массивом")
                    return False

                if success:
                    self.connection.commit()
                    logger.info("Данные успешно загружены в БД")
                else:
                    self.connection.rollback()
                    logger.error("Ошибка загрузки данных, откат изменений")

                return success

            except Exception as e:
                self.connection.rollback()
                logger.error(f"Критическая ошибка, откат транзакции: {e}")
                return False
            finally:
                cursor.close()

        except Exception as e:
            logger.error(f"Ошибка загрузки файла {data}: {e}")
            return False
        finally:
            self.close_connection()

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Получает товар по ID в JSON формате"""
        try:
            if not self.connect_to_db():
                return None

            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            # Используем готовую функцию из БД
            cursor.execute("SELECT get_product_json(%s) as product_data", (product_id,))
            result = cursor.fetchone()

            cursor.close()
            return result["product_data"] if result else None

        except Exception as e:
            logger.error(f"Ошибка получения продукта {product_id}: {e}")
            return None
        finally:
            self.close_connection()


loader = KlarsteinProductLoader(DB_CONFIG)
