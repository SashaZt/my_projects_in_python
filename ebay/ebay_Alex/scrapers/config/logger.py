# config/logger.py
# Размещать в папке config
import sys
from pathlib import Path

from loguru import logger


def setup_logging():
    """Настройка логирования для всего приложения"""
    # Находим директорию, где находится файл logger.py
    current_file_path = Path(__file__)

    # Перемещаемся на уровень выше относительно родительской директории (config)
    # Сначала получаем родительскую директорию (config), затем ее родителя (корень проекта)
    project_root = current_file_path.parent.parent

    # Создаем директорию для логов на уровне корня проекта
    log_directory = project_root / "log"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file_path = log_directory / "log_message.log"

    logger.remove()  # Удаляем все обработчики

    # Логирование в файл с добавлением имени файла
    logger.add(
        log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}",
        level="DEBUG",
        encoding="utf-8",
        rotation="10 MB",
        retention="7 days",
    )

    # Логирование в консоль (цветной вывод) с добавлением имени файла
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{file}:{line}</cyan> | <cyan>{message}</cyan>",
        level="DEBUG",
        enqueue=True,
    )

    return logger


# Создаем и настраиваем экземпляр логгера при импорте модуля
logger = setup_logging()
