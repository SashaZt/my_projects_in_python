import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from logger import logger


def load_json_data(json_content: str) -> Dict[str, Any]:
    """
    Загружает данные из JSON строки

    Args:
        json_content (str): Содержимое JSON файла

    Returns:
        dict: Загруженные данные
    """
    try:
        # Проверяем, если json_content - это строка, содержащая json в виде строки
        # (такое может произойти, если JSON был сохранен как строка внутри JSON)
        if json_content.startswith('"') and json_content.endswith('"'):
            # Удаляем внешние кавычки и экранированные символы
            json_content = json_content[1:-1].replace("\\n", "\n").replace('\\"', '"')

        return json.loads(json_content)
    except Exception as e:
        logger.error(f"Ошибка при загрузке JSON: {e}")
        return {}


def save_json_data(data: Dict[str, Any], output_file: str) -> bool:
    """
    Сохраняет данные в JSON файл

    Args:
        data (dict): Данные для сохранения
        output_file (str): Путь к выходному файлу

    Returns:
        bool: True если сохранение успешно, иначе False
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении JSON: {e}")
        return False


def extract_product_info_from_json(json_path: str) -> Dict[str, Any]:
    """
    Извлекает информацию о продукте из JSON файла

    Args:
        json_path (str): Путь к JSON файлу

    Returns:
        dict: Структурированные данные о продукте
    """
    try:
        # Проверяем, существует ли файл
        json_file = Path(json_path)
        if not json_file.exists():
            logger.error(f"Файл не найден: {json_path}")
            return {}

        # Читаем JSON файл
        with open(json_file, "r", encoding="utf-8") as file:
            content = file.read()

        # Загружаем данные из JSON
        data = load_json_data(content)

        return data
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных из JSON файла: {e}")
        return {}


def create_product_database(json_directory: str, output_file: str) -> None:
    """
    Создает базу данных продуктов из нескольких JSON файлов

    Args:
        json_directory (str): Путь к директории с JSON файлами
        output_file (str): Путь к выходному файлу базы данных
    """
    json_path = Path(json_directory)
    products = []

    # Обрабатываем все JSON файлы
    for json_file in json_path.glob("*.json"):
        try:
            logger.info(f"Добавление продукта из файла: {json_file}")

            # Извлекаем данные из JSON файла
            product_data = extract_product_info_from_json(json_file)

            if product_data:
                products.append(product_data)
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {json_file}: {e}")

    # Сохраняем базу данных в файл
    with open(output_file, "w", encoding="utf-8") as db_file:
        json.dump(products, db_file, ensure_ascii=False, indent=4)

    logger.info(f"База данных успешно создана и сохранена в {output_file}")
