# Экспортируем модули для удобства импорта
from .logger import logger
from .config import Config

__all__ = ["Config", "logger"]
