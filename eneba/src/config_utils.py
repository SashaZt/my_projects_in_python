# config_utils.py
import json
from pathlib import Path

from logger import logger

# Базовая директория — текущая рабочая директория
BASE_DIR = Path.cwd()


def load_config(config_file="config/config.json"):
    """Загружает пути из JSON-конфига и возвращает словари с объектами Path."""
    config_path = BASE_DIR / config_file

    # Читаем конфигурацию
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Формируем пути
    directories = {
        key: BASE_DIR / value for key, value in config["directories"].items()
    }

    # Создаём директории
    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Директория готова: {dir_path}")

    return config
