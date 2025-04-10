# src/path_manager.py
"""
Модуль для централизованного управления путями файлов и директорий.
Предоставляет функции для инициализации и получения путей на основе выбранной категории.
"""

from pathlib import Path

from category_manager import category_manager
from config_utils import load_config
from logger import logger

# Загружаем конфигурацию
config = load_config()
BASE_DIR = Path(__file__).parent.parent

# Глобальные переменные для хранения путей
paths = {
    "url": None,
    "html_page": None,
    "html_product": None,
    "json_dir": None,
    "output_json": None,
    "output_xlsx": None,
    "export_xlsx": None,
    "new_output_xlsx": None,
    "bd_json": None,
    "temp_json": None,
    "start_page": None,
    "num_pages": None,
    "delay": None,
    "category_id": None,
    "category_name": None,
}


def init_paths(category_id=None):
    """
    Инициализирует все пути на основе выбранной категории

    Args:
        category_id (str, optional): ID категории или ключ категории

    Returns:
        bool: True если инициализация прошла успешно, иначе False
    """
    global paths

    # Устанавливаем текущую категорию, если указан category_id
    if category_id:
        if not category_manager.set_current_category(category_id):
            logger.error(f"Не удалось установить категорию {category_id}")
            return False

    # Если категория не установлена, сообщаем об ошибке
    if not category_manager.current_category:
        logger.error("Текущая категория не установлена")
        return False

    # Получаем информацию о категории
    category_info = category_manager.get_current_category_info()
    if not category_info:
        logger.error("Не удалось получить информацию о текущей категории")
        return False

    # Получаем пути для директорий
    paths["html_page"] = category_manager.get_category_page_dir()
    paths["html_product"] = category_manager.get_category_html_dir()
    paths["json_dir"] = category_manager.get_category_json_dir()

    # Получаем пути для файлов
    category_files = category_manager.get_category_data_files()
    if not category_files:
        logger.error("Не удалось получить пути к файлам для текущей категории")
        return False

    # Заполняем все пути
    paths["url"] = category_manager.get_category_url()
    paths["export_xlsx"] = category_files["export_xlsx"]
    paths["output_json"] = category_files["output_json"]
    paths["output_xlsx"] = category_files["output_xlsx"]
    paths["new_output_xlsx"] = category_files["new_output_xlsx"]
    paths["bd_json"] = category_files["bd_json"]
    paths["temp_json"] = category_files["temp_json"]
    paths["export_xlsx"] = category_files.get("export_xlsx")  # Может отсутствовать

    # Получаем параметры категории
    paths["start_page"] = int(category_manager.get_category_start_page())
    paths["num_pages"] = int(category_manager.get_category_url_pages())
    paths["delay"] = int(category_manager.get_category_url_delay())
    paths["category_id"] = category_info.get("id")
    paths["category_name"] = category_info.get("name")

    # Создаем все необходимые директории
    paths["html_page"].mkdir(parents=True, exist_ok=True)
    paths["html_product"].mkdir(parents=True, exist_ok=True)
    paths["json_dir"].mkdir(parents=True, exist_ok=True)

    logger.info(
        f"Пути инициализированы для категории: {paths['category_name']} (ID: {paths['category_id']})"
    )
    return True


def get_path(path_name):
    """
    Получает значение пути по его имени

    Args:
        path_name (str): Имя пути ('url', 'html_page', etc.)

    Returns:
        any: Значение пути или None, если путь не найден
    """
    if path_name in paths:
        if paths[path_name] is None:
            logger.warning(
                f"Путь '{path_name}' не инициализирован. Вызовите init_paths() перед использованием."
            )
        return paths[path_name]
    else:
        logger.error(f"Неизвестное имя пути: {path_name}")
        return None


def get_all_paths():
    """
    Возвращает все инициализированные пути

    Returns:
        dict: Словарь со всеми путями
    """
    return paths


def is_initialized():
    """
    Проверяет, инициализированы ли пути

    Returns:
        bool: True если пути инициализированы, иначе False
    """
    return paths["category_id"] is not None


def select_category_and_init_paths():
    """
    Интерактивно предлагает пользователю выбрать категорию и инициализирует пути

    Returns:
        dict: Информация о выбранной категории или None в случае ошибки
    """
    categories = category_manager.get_categories()
    print("\nДоступные категории:")
    for i, (cat_id, cat_info) in enumerate(categories.items(), 1):
        print(f"{i}. {cat_info['name']} (ID: {cat_info['id']})")

    try:
        cat_choice = int(input("\nВыберите категорию (номер): "))
        cat_keys = list(categories.keys())
        selected_category = cat_keys[cat_choice - 1]

        if init_paths(selected_category):
            return category_manager.get_current_category_info()
        else:
            print("Не удалось инициализировать пути для выбранной категории")
            return None
    except (ValueError, IndexError):
        print("Некорректный выбор категории")
        return None
