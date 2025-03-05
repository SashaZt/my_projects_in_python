import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from models import Config, Metadata

# Пути к директориям и файлам
current_directory = Path.cwd()
data_directory = current_directory / "data"
log_directory = current_directory / "log"
config_directory = current_directory / "config"
db_directory = current_directory / "db"
CONFIG_PATH = config_directory / "config.json"

# Глобальные переменные
metadata = None
config = None


def setup_directories():
    """Инициализация директорий для хранения данных и логов."""
    db_directory.mkdir(parents=True, exist_ok=True)
    data_directory.mkdir(parents=True, exist_ok=True)
    log_directory.mkdir(parents=True, exist_ok=True)
    config_directory.mkdir(parents=True, exist_ok=True)


def setup_logging():
    """Настройка логирования."""
    logger.remove()
    logger.add(
        log_directory / "log_message.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
        level="DEBUG",
        encoding="utf-8",
        rotation="10 MB",
        retention="7 days",
    )
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
        level="DEBUG",
        enqueue=True,
    )


def load_config() -> Config:
    """Загрузка конфигурации из JSON-файла."""
    global config

    try:
        # Проверяем, существует ли файл конфигурации
        if not os.path.exists(CONFIG_PATH):
            logger.error(f"Ошибка: файл конфигурации не найден: {CONFIG_PATH}")
            logger.error("Создайте файл конфигурации на основе примера.")
            sys.exit(1)

        # Загружаем конфигурацию
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # Проверяем наличие необходимых разделов
        required_sections = ["database", "google_sheets", "salesdrive"]
        for section in required_sections:
            if section not in config_data:
                logger.error(
                    f"Ошибка: в файле конфигурации отсутствует раздел '{section}'"
                )
                sys.exit(1)

        # Проверяем наличие необходимых параметров
        if "path" not in config_data["database"]:
            logger.error("Ошибка: не указан путь к базе данных (database.path)")
            sys.exit(1)

        if "credentials_path" not in config_data["google_sheets"]:
            logger.error(
                "Ошибка: не указан путь к учетным данным Google (google_sheets.credentials_path)"
            )
            sys.exit(1)

        if "spreadsheet_id" not in config_data["google_sheets"]:
            logger.error(
                "Ошибка: не указан ID таблицы Google Sheets (google_sheets.spreadsheet_id)"
            )
            sys.exit(1)

        if "api" not in config_data["salesdrive"]:
            logger.error("Ошибка: не указан API ключ SalesDrive (salesdrive.api)")
            sys.exit(1)

        config = Config(**config_data)
        return config

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при чтении файла конфигурации: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при загрузке конфигурации: {e}")
        sys.exit(1)


def load_metadata_from_json(json_data: Dict[str, Any]) -> Metadata:
    """
    Загружает метаданные из JSON-данных, полученных от SalesDrive.

    Args:
        json_data: Словарь с данными из SalesDrive, содержащий ключи 'data' и 'meta'

    Returns:
        Объект с обработанными метаданными
    """
    global metadata

    # Если метаданные уже загружены, вернем их
    if metadata is not None:
        return metadata

    try:
        # Проверяем наличие метаданных в JSON
        if "meta" not in json_data:
            logger.error("В JSON-данных отсутствует секция 'meta'")
            return Metadata()

        meta_section = json_data["meta"]

        # Проверяем наличие полей в метаданных
        if "fields" not in meta_section:
            logger.error("В метаданных отсутствует секция 'fields'")
            return Metadata()

        fields = meta_section["fields"]

        # Создаем объект для хранения обработанных метаданных
        processed_metadata = Metadata()

        # Обрабатываем tipProdazu1
        if "tipProdazu1" in fields:
            tip_field = fields["tipProdazu1"]
            options = tip_field.get("options", [])

            # Создаем соответствие ID -> текст
            tip_mapping = {}
            for option in options:
                value = option.get("value")
                text = option.get("text")
                if value is not None and text:
                    tip_mapping[value] = text

            processed_metadata.tipProdazu1 = tip_mapping
            logger.info(f"Загружено {len(tip_mapping)} вариантов tipProdazu1")

        # Обрабатываем typeId
        if "typeId" in fields:
            type_field = fields["typeId"]
            options = type_field.get("options", [])

            # Создаем соответствие ID -> текст
            type_mapping = {}
            for option in options:
                value = option.get("value")
                text = option.get("text")
                if value is not None and text:
                    type_mapping[value] = text

            processed_metadata.typeId = type_mapping
            logger.info(f"Загружено {len(type_mapping)} вариантов typeId")

        # Обрабатываем statusId
        if "statusId" in fields:
            type_field = fields["statusId"]
            options = type_field.get("options", [])

            # Создаем соответствие ID -> текст
            type_mapping = {}
            for option in options:
                value = option.get("value")
                text = option.get("text")
                if value is not None and text:
                    type_mapping[value] = text

            processed_metadata.statusId = type_mapping
            logger.info(f"Загружено {len(type_mapping)} вариантов statusId")

        # Обрабатываем shipping_method
        if "shipping_method" in fields:
            type_field = fields["shipping_method"]
            options = type_field.get("options", [])

            # Создаем соответствие ID -> текст
            type_mapping = {}
            for option in options:
                value = option.get("value")
                text = option.get("text")
                if value is not None and text:
                    type_mapping[value] = text

            processed_metadata.shipping_method = type_mapping
            logger.info(f"Загружено {len(type_mapping)} вариантов shipping_method")

        # Обрабатываем payment_method
        if "payment_method" in fields:
            type_field = fields["payment_method"]
            options = type_field.get("options", [])

            # Создаем соответствие ID -> текст
            type_mapping = {}
            for option in options:
                value = option.get("value")
                text = option.get("text")
                if value is not None and text:
                    type_mapping[value] = text

            processed_metadata.payment_method = type_mapping
            logger.info(f"Загружено {len(type_mapping)} вариантов payment_method")

        # Сохраняем обработанные метаданные в глобальную переменную
        metadata = processed_metadata

        return processed_metadata

    except Exception as e:
        logger.error(f"Ошибка при обработке метаданных: {e}")
        return Metadata()


def write_json_to_file(file_path: Union[str, Path], data: Any) -> None:
    """Сохраняет данные в JSON файл."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def format_order_time_look(order_time: Optional[str]) -> str:
    """
    Форматирует время заказа в формат MM.YYYY.

    Args:
        order_time: Строка времени в формате 'YYYY-MM-DD HH:MM:SS'

    Returns:
        Строка в формате 'MM.YYYY' или пустая строка в случае ошибки
    """
    if not order_time:
        return ""

    try:
        # Парсим дату из строки формата "2024-08-03 09:22:04"
        dt = datetime.strptime(order_time, "%Y-%m-%d %H:%M:%S")
        # Форматируем в нужный формат "08.2024"
        return dt.strftime("%m.%Y")
    except Exception as e:
        logger.error(f"Ошибка при форматировании даты: {e}")
        return ""


def parse_order_date(order_time: Optional[str]) -> Dict[str, Optional[Union[str, int]]]:
    """
    Парсит дату заказа и возвращает различные форматы и компоненты.

    Args:
        order_time: Строка времени в формате 'YYYY-MM-DD HH:MM:SS'

    Returns:
        Словарь с разными форматами даты и её компонентами
    """
    result = {
        "sale_date": None,
        "day": None,
        "month": None,
        "year": None,
        "quarter": None,
        "month_year": None,
    }

    if not order_time:
        return result

    try:
        # Парсим и форматируем дату
        dt = datetime.strptime(order_time, "%Y-%m-%d %H:%M:%S")
        result["sale_date"] = dt.strftime("%Y-%m-%d")
        result["day"] = dt.day
        result["month"] = dt.month
        result["year"] = dt.year

        # Вычисляем квартал (1-4)
        result["quarter"] = (dt.month - 1) // 3 + 1

        # Формат месяц.год
        result["month_year"] = dt.strftime("%m.%Y")

        return result
    except Exception as e:
        logger.error(f"Ошибка при парсинге даты заказа: {e}")
        return result


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Безопасно получает значение из словаря.

    Args:
        data: Словарь с данными
        key: Ключ для получения значения
        default: Значение по умолчанию, если ключ отсутствует

    Returns:
        Значение из словаря или значение по умолчанию
    """
    return data.get(key, default)


def cache_metadata(
    metadata_data: Metadata, cache_file: str = "metadata_cache.json"
) -> None:
    """
    Кеширование метаданных в JSON файл.

    Args:
        metadata_data: Данные метаданных
        cache_file: Путь к файлу кеша
    """
    cache_path = data_directory / cache_file
    try:
        # Конвертируем dataclass в словарь
        metadata_dict = {
            "tipProdazu1": metadata_data.tipProdazu1,
            "typeId": metadata_data.typeId,
            "statusId": metadata_data.statusId,
            "shipping_method": metadata_data.shipping_method,
            "payment_method": metadata_data.payment_method,
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(metadata_dict, f, ensure_ascii=False, indent=4)
        logger.info(f"Метаданные успешно кешированы в {cache_path}")
    except Exception as e:
        logger.error(f"Ошибка при кешировании метаданных: {e}")


def load_cached_metadata(cache_file: str = "metadata_cache.json") -> Optional[Metadata]:
    """
    Загрузка кешированных метаданных из JSON файла.

    Args:
        cache_file: Путь к файлу кеша

    Returns:
        Объект Metadata или None в случае ошибки
    """
    cache_path = data_directory / cache_file
    try:
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                metadata_dict = json.load(f)
                metadata_obj = Metadata(
                    tipProdazu1=metadata_dict.get("tipProdazu1", {}),
                    typeId=metadata_dict.get("typeId", {}),
                    statusId=metadata_dict.get("statusId", {}),
                    shipping_method=metadata_dict.get("shipping_method", {}),
                    payment_method=metadata_dict.get("payment_method", {}),
                )
                logger.info(f"Загружены кешированные метаданные из {cache_path}")
                return metadata_obj
        return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке кешированных метаданных: {e}")
        return None


def log_performance_stats(task_name: str, start_time: float) -> None:
    """
    Логирует статистику производительности выполнения задачи.

    Args:
        task_name: Название задачи
        start_time: Время начала выполнения задачи (time.time())
    """
    elapsed_time = time.time() - start_time
    logger.info(f"Задача '{task_name}' выполнена за {elapsed_time:.2f} секунд")
