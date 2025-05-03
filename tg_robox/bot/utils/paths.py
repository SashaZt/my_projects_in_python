# bot/utils/paths.py
import os
import sys
from pathlib import Path

# Определяем корневую директорию проекта
ROOT_DIR = Path(__file__).parent.parent.absolute()


# Функция для добавления корня проекта в sys.path
def setup_paths():
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    return ROOT_DIR


# Вызываем функцию при импорте модуля
setup_paths()
