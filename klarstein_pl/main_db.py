import json
import re
from typing import Any, Dict, List, Optional

import psycopg2
from config.logger import logger
from psycopg2.extras import execute_values

# Конфигурация подключения к БД
DB_CONFIG = {
    "host": "localhost",
    "database": "klarstein_pl",
    "user": "klarstein_pl_user",
    "password": "Pqm36q1kmcAlsVMIp2glEdfwNnj69X",
    "port": 5431,
}


class KlarsteinProductLoader:
    """Класс для загрузки продуктов Klarstein в PostgreSQL"""

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

    def extract_product_id_from_sku(self, sku: str) -> int:
        """Извлекает product_id из SKU"""
        # Убираем префикс Kla и извлекаем числовую часть
        sku_clean = sku.replace("Kla", "").replace("kla", "")
        match = re.search(r"(\d+)", sku_clean)
        if match:
            return int(match.group(1))
        else:
            # Если не найдено число, используем хеш от SKU
            return abs(hash(sku)) % (2**31)

    def insert_product(self, cursor, product_data: Dict[str, Any]) -> Optional[int]:
        """Вставляет основную информацию о продукте"""
        try:
            sku = product_data.get("sku", "")
            if not sku:
                logger.warning("SKU отсутствует в данных продукта")
                return None

            product_id = self.extract_product_id_from_sku(sku)
            name_pl = product_data.get("name_pl", "")
            price = product_data.get("price")

            # Конвертируем цену в число
            if price:
                try:
                    price = float(str(price).replace(",", "."))
                except (ValueError, TypeError):
                    price = None

            insert_query = """
                INSERT INTO products (product_id, sku, name_pl, price)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (product_id) DO UPDATE SET
                    sku = EXCLUDED.sku,
                    name_pl = EXCLUDED.name_pl,
                    price = EXCLUDED.price,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING product_id
            """

            cursor.execute(insert_query, (product_id, sku, name_pl, price))
            result = cursor.fetchone()

            if result:
                logger.info(
                    f"Продукт {sku} (ID: {product_id}) успешно вставлен/обновлен"
                )
                return result[0]
            else:
                logger.error(f"Не удалось вставить продукт {sku}")
                return None

        except Exception as e:
            logger.error(
                f"Ошибка при вставке продукта {product_data.get('sku', 'unknown')}: {e}"
            )
            return None

    def insert_product_images(self, cursor, product_id: int, images: List[str]) -> bool:
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

    def insert_product_breadcrumbs(
        self, cursor, product_id: int, breadcrumbs: List[str]
    ) -> bool:
        """Вставляет хлебные крошки продукта"""
        try:
            # Удаляем существующие хлебные крошки
            cursor.execute(
                "DELETE FROM product_breadcrumbs WHERE product_id = %s", (product_id,)
            )

            if not breadcrumbs:
                return True

            # Подготавливаем данные
            breadcrumbs_data = []
            for order, breadcrumb in enumerate(breadcrumbs, 1):
                if breadcrumb and breadcrumb.strip():
                    breadcrumbs_data.append((product_id, breadcrumb.strip(), order))

            if breadcrumbs_data:
                insert_query = """
                    INSERT INTO product_breadcrumbs (product_id, breadcrumb_name, breadcrumb_order)
                    VALUES %s
                """
                execute_values(cursor, insert_query, breadcrumbs_data)
                logger.info(
                    f"Добавлено {len(breadcrumbs_data)} хлебных крошек для товара {product_id}"
                )

            return True

        except Exception as e:
            logger.error(
                f"Ошибка при вставке хлебных крошек для продукта {product_id}: {e}"
            )
            return False

    def insert_description_sections(
        self, cursor, product_id: int, sections: List[Dict[str, str]]
    ) -> bool:
        """Вставляет секции описания продукта"""
        try:
            # Удаляем существующие секции
            cursor.execute(
                "DELETE FROM product_description_sections WHERE product_id = %s",
                (product_id,),
            )

            if not sections:
                return True

            # Подготавливаем данные
            sections_data = []
            for order, section in enumerate(sections, 1):
                title_pl = section.get("title_pl", "").strip()
                description_pl = section.get("description_pl", "").strip()

                if title_pl and description_pl:
                    sections_data.append((product_id, title_pl, description_pl, order))

            if sections_data:
                insert_query = """
                    INSERT INTO product_description_sections (product_id, title_pl, description_pl, section_order)
                    VALUES %s
                """
                execute_values(cursor, insert_query, sections_data)
                logger.info(
                    f"Добавлено {len(sections_data)} секций описания для товара {product_id}"
                )

            return True

        except Exception as e:
            logger.error(
                f"Ошибка при вставке секций описания для продукта {product_id}: {e}"
            )
            return False

    def insert_specifications(
        self, cursor, product_id: int, specifications: Dict[str, str]
    ) -> bool:
        """Вставляет характеристики продукта"""
        try:
            # Удаляем существующие характеристики
            cursor.execute(
                "DELETE FROM product_specifications WHERE product_id = %s",
                (product_id,),
            )

            if not specifications:
                return True

            # Подготавливаем данные
            specs_data = []
            for spec_name, spec_value in specifications.items():
                if spec_name and str(spec_value).strip():
                    specs_data.append(
                        (product_id, spec_name.strip(), str(spec_value).strip())
                    )

            if specs_data:
                insert_query = """
                    INSERT INTO product_specifications (product_id, spec_name, spec_value)
                    VALUES %s
                """
                execute_values(cursor, insert_query, specs_data)
                logger.info(
                    f"Добавлено {len(specs_data)} характеристик для товара {product_id}"
                )

            return True

        except Exception as e:
            logger.error(
                f"Ошибка при вставке характеристик для продукта {product_id}: {e}"
            )
            return False

    def process_single_product(self, cursor, product_data: Dict[str, Any]) -> bool:
        """Обрабатывает один продукт"""
        try:
            # Извлекаем данные в зависимости от структуры
            if "product" in product_data:
                # Новый формат с вложенной структурой
                product_info = product_data["product"]
                breadcrumbs = product_data.get("breadcrumbs_pl", [])
                descriptions = product_data.get("description_pl", [])
                specifications = product_data.get("product_specifications", {})
            else:
                # Прямой формат
                product_info = product_data
                breadcrumbs = product_data.get("breadcrumbs_pl", [])
                descriptions = product_data.get("description_pl", [])
                specifications = product_data.get("product_specifications", {})

            sku = product_info.get("sku")
            if not sku:
                logger.warning("Продукт не имеет SKU, пропускаем")
                return False

            logger.info(f"Обработка продукта: {sku}")

            # 1. Вставляем основную информацию
            product_id = self.insert_product(cursor, product_info)
            if not product_id:
                return False

            # 2. Вставляем изображения
            images = product_info.get("images", [])
            if not self.insert_product_images(cursor, product_id, images):
                return False

            # 3. Вставляем хлебные крошки
            if not self.insert_product_breadcrumbs(cursor, product_id, breadcrumbs):
                return False

            # 4. Вставляем секции описания
            if not self.insert_description_sections(cursor, product_id, descriptions):
                return False

            # 5. Вставляем характеристики
            if not self.insert_specifications(cursor, product_id, specifications):
                return False

            logger.info(f"Продукт {sku} успешно обработан")
            return True

        except Exception as e:
            logger.error(f"Ошибка обработки продукта: {e}")
            return False

    def load_json_file(self, json_file_path: str) -> bool:
        """Загружает данные из JSON файла в базу данных"""
        try:
            # Читаем JSON файл
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Определяем структуру данных
            if isinstance(data, dict):
                if "product" in data or "sku" in data:
                    # Один продукт
                    products_data = [data]
                else:
                    logger.error("Неизвестная структура JSON")
                    return False
            elif isinstance(data, list):
                # Массив продуктов
                products_data = data
            else:
                logger.error("JSON должен быть объектом или массивом")
                return False

            logger.info(
                f"Найдено {len(products_data)} продуктов в файле {json_file_path}"
            )

            # Подключаемся к БД
            if not self.connect_to_db():
                return False

            cursor = self.connection.cursor()
            success_count = 0
            error_count = 0

            try:
                for i, product_data in enumerate(products_data, 1):
                    try:
                        # Начинаем транзакцию для каждого продукта
                        cursor.execute("SAVEPOINT product_savepoint")

                        if self.process_single_product(cursor, product_data):
                            cursor.execute("RELEASE SAVEPOINT product_savepoint")
                            success_count += 1
                        else:
                            cursor.execute("ROLLBACK TO SAVEPOINT product_savepoint")
                            error_count += 1

                    except Exception as e:
                        cursor.execute("ROLLBACK TO SAVEPOINT product_savepoint")
                        logger.error(f"Ошибка обработки продукта {i}: {e}")
                        error_count += 1

                # Подтверждаем все изменения
                self.connection.commit()

            except Exception as e:
                self.connection.rollback()
                logger.error(f"Критическая ошибка, откат транзакции: {e}")
                return False
            finally:
                cursor.close()

            logger.info(
                f"Загрузка завершена. Успешно: {success_count}, Ошибок: {error_count}"
            )
            return success_count > 0

        except Exception as e:
            logger.error(f"Ошибка загрузки файла {json_file_path}: {e}")
            return False
        finally:
            self.close_connection()

    def get_product_statistics(self) -> Dict[str, int]:
        """Возвращает статистику по загруженным продуктам"""
        try:
            if not self.connect_to_db():
                return {}

            cursor = self.connection.cursor()
            stats = {}

            # Статистика по таблицам
            tables_queries = {
                "products": "SELECT COUNT(*) FROM products",
                "product_images": "SELECT COUNT(*) FROM product_images",
                "product_breadcrumbs": "SELECT COUNT(*) FROM product_breadcrumbs",
                "product_description_sections": "SELECT COUNT(*) FROM product_description_sections",
                "product_specifications": "SELECT COUNT(*) FROM product_specifications",
            }

            for table, query in tables_queries.items():
                try:
                    cursor.execute(query)
                    stats[table] = cursor.fetchone()[0]
                except Exception as e:
                    logger.error(f"Ошибка получения статистики для {table}: {e}")
                    stats[table] = 0

            cursor.close()
            return stats

        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
        finally:
            self.close_connection()


def main():
    """Основная функция для тестирования"""
    # Создаем экземпляр загрузчика
    loader = KlarsteinProductLoader(DB_CONFIG)

    # Загружаем тестовые данные (замените на ваш путь к файлу)
    json_file_path = "Kla10035233.json"

    # Загружаем данные
    if loader.load_json_file(json_file_path):
        logger.info("Данные успешно загружены!")

        # Получаем статистику
        stats = loader.get_product_statistics()
        logger.info("Статистика по таблицам:")
        for table, count in stats.items():
            logger.info(f"  {table}: {count}")
    else:
        logger.error("Ошибка загрузки данных")


if __name__ == "__main__":
    main()
