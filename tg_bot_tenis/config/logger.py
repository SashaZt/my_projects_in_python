# config/logger.py - улучшенная версия
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger


class LoggerManager:
    """Управление логированием в проекте"""

    def __init__(self):
        self._logger = logger
        self._configured = False

    def setup_logging(
        self
    ) -> logger:
        """Настройка логирования для всего приложения"""
        if self._configured:
            return self._logger

            # Fallback - создаем log директорию в корне проекта
        project_root = Path(__file__).parent.parent
        log_directory = project_root / "log"
        log_directory.mkdir(parents=True, exist_ok=True)
        log_file_path = log_directory / "log_message.log"


        # Настройки по умолчанию
        defaults = {
            "level": "DEBUG",
            "rotation": "10 MB",
            "retention": "7 days",
            "format_file": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}",
            "format_console": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{file}:{line}</cyan> | <cyan>{message}</cyan>",
        }
        level = defaults["level"]
        rotation = defaults["rotation"]
        retention = defaults["retention"]
        format_file = defaults["format_file"]
        format_console = defaults["format_console"]

        self._logger.remove()

        # Логирование в файл
        self._logger.add(
            log_file_path,
            format=format_file,
            level=level,
            encoding="utf-8",
            rotation=rotation,
            retention=retention,
        )

        return self._logger

    def get_logger(self):
        """Получить настроенный логгер"""
        if not self._configured:
            # Автоматическая настройка с базовыми параметрами
            self.setup_logging()
        return self._logger


# Глобальный менеджер логгера
_logger_manager = LoggerManager()


def setup_logging():
    """Функция для настройки логирования"""
    return _logger_manager.setup_logging()


def get_logger():
    """Получить настроенный логгер"""
    return _logger_manager.get_logger()


def reconfigure_logging():
    """Пересконфигурировать логгер"""
    return _logger_manager.reconfigure()


# Создаем экземпляр логгера (будет настроен автоматически при первом использовании)
logger = get_logger()
