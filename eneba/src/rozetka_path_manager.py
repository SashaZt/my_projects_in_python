# src/rozetka_path_manager.py
"""
Модуль для централизованного управления путями файлов и директорий для Rozetka.
Предоставляет функции для инициализации и получения путей на основе выбранной категории Rozetka.
"""

from pathlib import Path

from config_utils import load_config
from logger import logger
from rozetka_manager import rozetka_manager

# Загружаем конфигурацию
config = load_config()
BASE_DIR = Path(__file__).parent.parent

# Глобальные переменные для хранения путей Rozetka
rozetka_paths = {
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


def init_rozetka_paths(category_id=None):
    """
    Инициализирует все пути Rozetka на основе выбранной категории

    Args:
        category_id (str, optional): ID категории Rozetka или ключ категории

    Returns:
        bool: True если инициализация прошла успешно, иначе False
    """
    global rozetka_paths

    # Устанавливаем текущую категорию, если указан category_id
    if category_id:
        if not rozetka_manager.set_current_category(category_id):
            logger.error(f"Не удалось установить категорию Rozetka {category_id}")
            return False

    # Если категория не установлена, сообщаем об ошибке
    if not rozetka_manager.current_category:
        logger.error("Текущая категория Rozetka не установлена")
        return False

    # Получаем информацию о категории
    category_info = rozetka_manager.get_current_category_info()
    if not category_info:
        logger.error("Не удалось получить информацию о текущей категории Rozetka")
        return False

    # Получаем пути для директорий
    rozetka_paths["html_page"] = rozetka_manager.get_category_page_dir()
    rozetka_paths["html_product"] = rozetka_manager.get_category_html_dir()
    rozetka_paths["json_dir"] = rozetka_manager.get_category_json_dir()

    # Получаем пути для файлов
    category_files = rozetka_manager.get_category_data_files()
    if not category_files:
        logger.error("Не удалось получить пути к файлам для текущей категории Rozetka")
        return False

    # Заполняем все пути
    rozetka_paths["url"] = rozetka_manager.get_category_url()
    rozetka_paths["output_json"] = category_files["output_json"]
    rozetka_paths["output_xlsx"] = category_files["output_xlsx"]
    rozetka_paths["export_xlsx"] = category_files["export_xlsx"]
    rozetka_paths["new_output_xlsx"] = category_files["new_output_xlsx"]
    rozetka_paths["bd_json"] = category_files["bd_json"]
    rozetka_paths["temp_json"] = category_files["temp_json"]

    # Получаем параметры категории
    rozetka_paths["start_page"] = int(rozetka_manager.get_category_start_page())
    rozetka_paths["num_pages"] = int(rozetka_manager.get_category_url_pages())
    rozetka_paths["delay"] = int(rozetka_manager.get_category_url_delay())
    rozetka_paths["category_id"] = category_info.get("id")
    rozetka_paths["category_name"] = category_info.get("name")

    # Создаем все необходимые директории
    rozetka_paths["html_page"].mkdir(parents=True, exist_ok=True)
    rozetka_paths["html_product"].mkdir(parents=True, exist_ok=True)
    rozetka_paths["json_dir"].mkdir(parents=True, exist_ok=True)

    logger.info(
        f"Пути Rozetka инициализированы для категории: {rozetka_paths['category_name']} (ID: {rozetka_paths['category_id']})"
    )
    return True


def get_rozetka_path(path_name):
    """
    Получает значение пути Rozetka по его имени

    Args:
        path_name (str): Имя пути ('url', 'html_page', etc.)

    Returns:
        any: Значение пути или None, если путь не найден
    """
    if path_name in rozetka_paths:
        if rozetka_paths[path_name] is None:
            logger.warning(
                f"Путь Rozetka '{path_name}' не инициализирован. Вызовите init_rozetka_paths() перед использованием."
            )
            logger.info(rozetka_paths[path_name])
        return rozetka_paths[path_name]
    else:
        logger.error(f"Неизвестное имя пути Rozetka: {path_name}")
        return None


def get_all_rozetka_paths():
    """
    Возвращает все инициализированные пути Rozetka

    Returns:
        dict: Словарь со всеми путями Rozetka
    """
    return rozetka_paths.copy()


def is_rozetka_initialized():
    """
    Проверяет, инициализированы ли пути Rozetka

    Returns:
        bool: True если пути Rozetka инициализированы, иначе False
    """
    return rozetka_paths["category_id"] is not None


def select_rozetka_category_and_init_paths():
    """
    Интерактивно предлагает пользователю выбрать категорию Rozetka и инициализирует пути

    Returns:
        dict: Информация о выбранной категории Rozetka или None в случае ошибки
    """
    categories = rozetka_manager.get_categories()

    if not categories:
        print("Нет доступных категорий Rozetka в конфигурации")
        logger.warning("В конфигурации отсутствуют категории Rozetka")
        return None

    print("\nДоступные категории Rozetka:")
    for i, (cat_id, cat_info) in enumerate(categories.items(), 1):
        print(f"{i}. {cat_info['name']} (ID: {cat_info['id']})")

    try:
        cat_choice = int(input("\nВыберите категорию Rozetka (номер): "))
        cat_keys = list(categories.keys())

        if cat_choice < 1 or cat_choice > len(cat_keys):
            print("Номер категории вне допустимого диапазона")
            return None

        selected_category = cat_keys[cat_choice - 1]

        if init_rozetka_paths(selected_category):
            category_info = rozetka_manager.get_current_category_info()
            logger.info(
                f"Успешно выбрана и инициализирована категория Rozetka: {category_info['name']}"
            )
            return category_info
        else:
            print("Не удалось инициализировать пути для выбранной категории Rozetka")
            logger.error(
                f"Ошибка инициализации путей для категории Rozetka: {selected_category}"
            )
            return None
    except (ValueError, IndexError) as e:
        print("Некорректный выбор категории Rozetka")
        logger.error(f"Ошибка при выборе категории Rozetka: {str(e)}")
        return None


def reset_rozetka_paths():
    """
    Сбрасывает все пути Rozetka к начальному состоянию
    """
    global rozetka_paths

    for key in rozetka_paths:
        rozetka_paths[key] = None

    rozetka_manager.current_category = None
    logger.info("Пути Rozetka сброшены к начальному состоянию")


def get_rozetka_category_info():
    """
    Возвращает информацию о текущей выбранной категории Rozetka

    Returns:
        dict: Информация о категории или None если категория не выбрана
    """
    if not is_rozetka_initialized():
        logger.warning("Категория Rozetka не инициализирована")
        return None

    return {
        "category_id": rozetka_paths["category_id"],
        "category_name": rozetka_paths["category_name"],
        "url": rozetka_paths["url"],
        "start_page": rozetka_paths["start_page"],
        "num_pages": rozetka_paths["num_pages"],
        "delay": rozetka_paths["delay"],
    }


def print_rozetka_paths_status():
    """
    Выводит текущий статус путей Rozetka в читаемом формате
    """
    if not is_rozetka_initialized():
        print("Пути Rozetka не инициализированы")
        return

    print(f"\n=== Статус путей Rozetka ===")
    print(
        f"Категория: {rozetka_paths['category_name']} (ID: {rozetka_paths['category_id']})"
    )
    print(f"URL: {rozetka_paths['url']}")
    print(
        f"Страницы: {rozetka_paths['start_page']}-{rozetka_paths['start_page'] + rozetka_paths['num_pages'] - 1}"
    )
    print(f"Задержка: {rozetka_paths['delay']} сек")
    print(f"HTML страницы: {rozetka_paths['html_page']}")
    print(f"HTML товары: {rozetka_paths['html_product']}")
    print(f"JSON: {rozetka_paths['json_dir']}")
    print(f"Выходной Excel: {rozetka_paths['output_xlsx']}")
    print("=" * 30)


def validate_rozetka_paths():
    """
    Проверяет корректность всех инициализированных путей Rozetka

    Returns:
        bool: True если все пути корректны, иначе False
    """
    if not is_rozetka_initialized():
        logger.error("Пути Rozetka не инициализированы для валидации")
        return False

    # Проверяем существование директорий
    directories_to_check = ["html_page", "html_product", "json_dir"]
    for dir_name in directories_to_check:
        dir_path = rozetka_paths[dir_name]
        if not dir_path or not dir_path.exists():
            logger.error(f"Директория Rozetka {dir_name} не существует: {dir_path}")
            return False

    # Проверяем наличие обязательных параметров
    required_params = [
        "url",
        "category_id",
        "category_name",
        "start_page",
        "num_pages",
        "delay",
    ]
    for param in required_params:
        if rozetka_paths[param] is None:
            logger.error(f"Обязательный параметр Rozetka {param} не установлен")
            return False

    logger.info("Все пути Rozetka прошли валидацию успешно")
    return True


def create_rozetka_directory_structure():
    """
    Создает всю необходимую структуру директорий для Rozetka
    """
    if not is_rozetka_initialized():
        logger.error(
            "Невозможно создать структуру директорий - пути Rozetka не инициализированы"
        )
        return False

    try:
        # Создаем основные рабочие директории
        rozetka_paths["html_page"].mkdir(parents=True, exist_ok=True)
        rozetka_paths["html_product"].mkdir(parents=True, exist_ok=True)
        rozetka_paths["json_dir"].mkdir(parents=True, exist_ok=True)

        # Создаем директорию для данных если её нет
        data_dir = rozetka_paths["output_xlsx"].parent
        data_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Структура директорий Rozetka успешно создана")
        return True

    except Exception as e:
        logger.error(f"Ошибка при создании структуры директорий Rozetka: {str(e)}")
        return False
