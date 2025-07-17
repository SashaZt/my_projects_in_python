# config/logger.py - улучшенная версия
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from .config import Config
    from .paths import ProjectPaths


class LoggerManager:
    """Управление логированием в проекте"""

    def __init__(self):
        self._logger = logger
        self._configured = False

    def setup_logging(
        self, paths: "ProjectPaths" = None, config: "Config" = None
    ) -> logger:
        """Настройка логирования для всего приложения"""
        if self._configured:
            return self._logger

        # Определяем путь для лог файла
        if paths is None:
            # Fallback - создаем log директорию в корне проекта
            project_root = Path(__file__).parent.parent
            log_directory = project_root / "log"
            log_directory.mkdir(parents=True, exist_ok=True)
            log_file_path = log_directory / "log_message.log"
        else:
            # Используем temp директорию из paths для логов
            log_file_path = paths.temp / "log_message.log"

        # Настройки по умолчанию
        defaults = {
            "level": "DEBUG",
            "rotation": "10 MB",
            "retention": "7 days",
            "format_file": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}",
            "format_console": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{file}:{line}</cyan> | <cyan>{message}</cyan>",
        }

        # Используем настройки из конфига, если доступны
        if config and hasattr(config, "logging"):
            log_config = config.logging
            level = log_config.level
            rotation = log_config.rotation
            retention = log_config.retention
            format_file = log_config.format_file
            format_console = log_config.format_console
        else:
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

        # Логирование в консоль (только если не production)
        show_console = True
        if config and hasattr(config, "environment"):
            show_console = config.environment != "production"

        if show_console:
            self._logger.add(
                sys.stderr,
                format=format_console,
                level=level,
                enqueue=True,
            )

        self._configured = True

        # Логируем информацию о запуске
        if config:
            self._logger.info(f"Запуск {config.project_name} v{config.version}")
            self._logger.info(f"Окружение: {config.environment}")
            self._logger.info(f"Логи сохраняются в: {log_file_path}")

        return self._logger

    def get_logger(self):
        """Получить настроенный логгер"""
        if not self._configured:
            # Автоматическая настройка с базовыми параметрами
            self.setup_logging()
        return self._logger

    def reconfigure(self, paths: "ProjectPaths" = None, config: "Config" = None):
        """Пересконфигурировать логгер"""
        self._configured = False
        return self.setup_logging(paths, config)


# Глобальный менеджер логгера
_logger_manager = LoggerManager()


def setup_logging(paths: "ProjectPaths" = None, config: "Config" = None):
    """Функция для настройки логирования"""
    return _logger_manager.setup_logging(paths, config)


def get_logger():
    """Получить настроенный логгер"""
    return _logger_manager.get_logger()


def reconfigure_logging(paths: "ProjectPaths" = None, config: "Config" = None):
    """Пересконфигурировать логгер"""
    return _logger_manager.reconfigure(paths, config)


# Создаем экземпляр логгера (будет настроен автоматически при первом использовании)
logger = get_logger()
