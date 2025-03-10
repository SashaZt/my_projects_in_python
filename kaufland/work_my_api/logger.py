import sys
from pathlib import Path

from loguru import logger


def setup_logging():
    """Настройка логирования для всего приложения"""
    current_directory = Path.cwd()
    log_directory = current_directory / "log"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file_path = log_directory / "log_message.log"

    logger.remove()  # Удаляем все обработчики

    # Логирование в файл
    logger.add(
        log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
        level="DEBUG",
        encoding="utf-8",
        rotation="10 MB",
        retention="7 days",
    )

    # Логирование в консоль (цветной вывод)
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
        level="DEBUG",
        enqueue=True,
    )

    return logger


# Создаем и настраиваем экземпляр логгера при импорте модуля
logger = setup_logging()
