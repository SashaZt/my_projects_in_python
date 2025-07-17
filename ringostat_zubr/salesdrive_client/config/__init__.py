# config/__init__.py
from .config import Config

# Инициализация глобальных объектов
config = Config.load()

# Настройка логирования с использованием config и paths

__all__ = [
    "config",

    "Config",
]
