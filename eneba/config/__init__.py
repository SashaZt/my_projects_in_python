# config/__init__.py
from .config import Config
from .logger import get_logger, setup_logging

# from .paths import ProjectPaths

# Инициализация глобальных объектов
config = Config.load()
# paths = ProjectPaths.from_config(config)

# Настройка логирования с использованием config и paths
# logger = setup_logging(paths, config)
logger = setup_logging(config)

__all__ = [
    "config",
    "paths",
    "logger",
    "Config",
    # "ProjectPaths",
    "setup_logging",
    "get_logger",
]
