# src/main_product.py

import json
import math
from pathlib import Path

from bs4 import BeautifulSoup
from category_manager import category_manager
from config_utils import load_config
from logger import logger
from main_bd import get_all_data_ukrainian_headers, update_prices_and_images
from path_manager import get_path, is_initialized, select_category_and_init_paths

# Базовая директория
BASE_DIR = Path(__file__).parent.parent
config = load_config()


def process_price_data(data):
    """Обработка данных из файла с ценами"""
    # logger.info("Обработка цен")
    try:
        # Если данные представлены как список (из файла), берем первый элемент
        if isinstance(data, list):
            data = data[0] if data else {}

        # Получаем объект response из структуры данных
        response = data.get("response", {})
        if not response:
            logger.error("В данных отсутствует ключ 'response'")
            return None

        # Получаем данные о продукте
        product_data = response.get("data", {}).get("wickedProductNoCache", {})
        if not product_data:
            logger.error("Не удалось найти данные о продукте")
            return None

        # Получаем список аукционов
        auctions = product_data.get("auctions", {}).get("edges", [])
        if not auctions:
            logger.warning("Список аукционов пуст")

            # Попробуем получить цену из preferredAuction, если он есть
            preferred_auction = product_data.get("preferredAuction", {})
            if preferred_auction:
                price = preferred_auction.get("price", {}).get("amount")
                if price:
                    logger.info(f"Получена цена из preferredAuction: {price/100} UAH")
                    return price / 100  # Цена в копейках, делим на 100
            return None

        # Собираем все цены из аукционов
        all_prices = []
        for edge in auctions:
            node = edge.get("node", {})
            price = node.get("price", {}).get("amount")
            if price:
                # Цена в копейках, делим на 100 для получения гривен
                all_prices.append(price / 100)
                # logger.debug(f"Найдена цена: {price/100} UAH")

        if not all_prices:
            logger.warning("Не найдено ни одной цены в аукционах")
            return None

        min_price = min(all_prices)
        # logger.info(f"Минимальная цена: {min_price} UAH")
        return min_price

    except Exception as e:
        logger.error(f"Ошибка при обработке цен: {str(e)}")
        return None


def parse_json_and_html_files():
    """Обрабатывает JSON и HTML файлы для текущей категории"""
    # Получаем пути для текущей категории
    html_product = get_path("html_product")
    json_dir = get_path("json_dir")
    bd_json = get_path("bd_json")
    output_path = get_path("output_xlsx")
    category_id = get_path("category_id")
    logger.info(f"Обрабатываем JSON файлы из: {json_dir}")
    logger.info(f"Ищем HTML файлы в: {html_product}")

    all_data = []
    json_files = list(json_dir.glob("*_price.json"))
    logger.info(f"Найдено {len(json_files)} JSON файлов для обработки")

    for json_file in json_files:
        filename = json_file.stem
        logger.debug(f"Обрабатываем файл: {filename}")

        # Разделяем имя файла по '_'
        parts = filename.split("_")
        if len(parts) < 2 or parts[-1] != "price":
            logger.warning(f"Некорректное имя файла: {filename}, пропускаем")
            continue

        # Убираем '_price' из имени для получения slug
        slug = "_".join(parts[:-1])

        # Открываем файл и загружаем данные
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data_json = json.load(f)
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {json_file}: {str(e)}")
            continue

        # Извлекаем цену
        price = process_price_data(data_json)
        # Преобразуем в число с плавающей точкой
        if not price:
            price = 0
        price_uah_float = float(price)
        # Округляем в большую сторону до целого
        price_uah_rounded = math.ceil(price_uah_float)
        price_uah = str(price_uah_rounded).replace(".", ",")

        # Ищем соответствующий HTML-файл по slug
        html_file = html_product / f"{slug}.html"

        if not html_file.exists():
            # Пробуем альтернативное имя
            html_file = html_product / f"{slug.replace('/', '_')}.html"
            if not html_file.exists():
                logger.warning(f"HTML-файл для {slug} не найден")
                # Добавляем запись без изображений
                result = {"slug": slug, "price": price_uah, "images": []}
                all_data.append(result)
                logger.info(
                    f"Обработан {slug}: цена={price_uah}, изображений=0 (HTML не найден)"
                )
                continue

        # Извлекаем данные Apollo State из HTML-файла
        apollo_data = scrap_html(html_file)

        if not apollo_data:
            logger.error(f"Не удалось извлечь данные Apollo State из {html_file}")
            # Добавляем запись без изображений
            result = {"slug": slug, "price": price_uah, "images": []}
            all_data.append(result)
            logger.info(
                f"Обработан {slug}: цена={price_uah}, изображений=0 (ошибка Apollo)"
            )
            continue

        # Извлекаем URL-адреса изображений
        image_urls = extract_media_urls(apollo_data)
        if not image_urls:
            image_urls = []

        # Формируем результат с ценой и URL-адресами изображений
        result = {"slug": slug, "price": price_uah, "images": image_urls}
        all_data.append(result)
        logger.info(
            f"Обработан {slug}: цена={price_uah}, изображений={len(image_urls)}"
        )

    # Сохраняем все данные в JSON-файл
    with open(bd_json, "w", encoding="utf-8") as out_file:
        json.dump(all_data, out_file, ensure_ascii=False, indent=4)

    logger.info(
        f"Данные сохранены в {bd_json}, всего обработано {len(all_data)} товаров"
    )
    return all_data, bd_json


def extract_media_urls(apollo_data):
    """
    Извлекает URL-адреса изображений из данных Apollo State

    Args:
        apollo_data (dict): Данные Apollo State

    Returns:
        list: Список URL-адресов изображений
    """
    media_urls = []

    # Ищем все продукты в данных
    for key, value in apollo_data.items():
        if key.startswith("Product::"):
            # Проверяем наличие медиа в продукте
            if 'media({"size":1920})' in value:
                media_objects = value['media({"size":1920})']

                # Проходим по всем объектам медиа
                for media_obj in media_objects:
                    # Если это объект с изображением (а не ссылка на YouTube видео)
                    if (
                        isinstance(media_obj, dict)
                        and media_obj.get("__typename") == "MultiSizeImage"
                    ):
                        # Добавляем URL изображения в список
                        if "src" in media_obj:
                            media_urls.append(media_obj["src"])

    return media_urls


def scrap_html(html_file):
    """
    Извлекает данные Apollo State из HTML файла

    Args:
        html_file (Path): Путь к HTML файлу
        output_json_file (Path, optional): Путь для сохранения JSON данных

    Returns:
        dict: Данные Apollo State или None
    """
    with open(html_file, "r", encoding="utf-8") as file:
        content = file.read()
    soup = BeautifulSoup(content, "lxml")
    # Поиск тега script с id="__APOLLO_STATE__"
    apollo_script = soup.find("script", {"id": "__APOLLO_STATE__"})

    if apollo_script:
        # Извлечение JSON-данных из тега script
        apollo_data = apollo_script.string

        # Проверка на пустые данные
        if apollo_data:
            # Преобразование данных в словарь Python
            try:
                data_dict = json.loads(apollo_data)
                return data_dict
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка декодирования JSON: {e}")
                return None
        else:
            logger.error("Тег Apollo State найден, но не содержит данных")
            return None
    else:
        logger.error("Тег Apollo State не найден в HTML")
        return None


def save_to_excel(data, output_path):
    """
    Сохраняет данные в Excel файл

    Args:
        data (list): Список словарей с данными
        output_path (str or Path): Путь для сохранения Excel файла

    Returns:
        bool: True, если сохранение успешно, иначе False
    """
    html_product = get_path("html_product")
    json_dir = get_path("json_dir")
    bd_json = get_path("bd_json")
    output_path = get_path("output_xlsx")
    category_id = get_path("category_id")
    try:
        import pandas as pd

        # Создаем DataFrame из списка словарей
        df = pd.DataFrame(data)

        # Сохраняем в Excel
        df.to_excel(output_path, index=False)

        logger.info(f"Данные успешно сохранены в {output_path}")
        return True

    except Exception as e:
        logger.error(f"Ошибка при сохранении в Excel: {str(e)}")
        return False


def export_data_to_excel(category_id=None):
    """
    Экспортирует данные из базы в Excel файл

    Args:
        category_id (str, optional): ID категории для фильтрации
    """
    # Получаем пути для текущей категории

    # Получаем данные из базы с украинскими заголовками
    data = get_all_data_ukrainian_headers(category_id=category_id)
    html_product = get_path("html_product")
    json_dir = get_path("json_dir")
    bd_json = get_path("bd_json")
    output_path = get_path("output_xlsx")
    category_id = get_path("category_id")
    if data:
        # Сохраняем данные в Excel
        success = save_to_excel(data, output_path)

        if success:
            logger.info(f"Данные успешно экспортированы в {output_path}")
        else:
            logger.error("Не удалось экспортировать данные в Excel")
    else:
        logger.warning("Нет данных для экспорта")


def init_category():
    """Инициализирует категорию на основе выбора пользователя"""
    categories = category_manager.get_categories()
    print("\nДоступные категории:")
    for i, (cat_id, cat_info) in enumerate(categories.items(), 1):
        print(f"{i}. {cat_info['name']} (ID: {cat_id})")

    try:
        cat_choice = int(input("\nВыберите категорию (номер): "))
        cat_keys = list(categories.keys())
        selected_category = cat_keys[cat_choice - 1]

        if not category_manager.set_current_category(selected_category):
            logger.error(f"Не удалось установить категорию {selected_category}")
            return None

        category_info = category_manager.get_current_category_info()
        logger.info(
            f"Выбрана категория: {category_info['name']} (ID: {category_info['id']})"
        )
        return category_info
    except (ValueError, IndexError):
        logger.error("Некорректный выбор категории")
        return None


if __name__ == "__main__":
    # Инициализация категории
    category_info = select_category_and_init_paths()

    category_id = get_path("category_id")
    if not category_info:
        logger.error("Не удалось инициализировать категорию")
        exit(1)

    # Собираем данные из JSON и HTML файлов
    all_data, bd_json_path = parse_json_and_html_files()

    if not all_data:
        logger.warning("Нет данных для обновления")
        exit(0)

    # Обновляем данные в БД
    updated_prices, updated_images, errors = update_prices_and_images(
        bd_json_path, category_id=category_id
    )

    logger.info(f"Обновление данных завершено:")
    logger.info(f"- Обновлено цен: {updated_prices}")
    logger.info(f"- Обновлено изображений: {updated_images}")
    logger.info(f"- Ошибок: {errors}")

    # Экспортируем в Excel для выбранной категории
    export_data_to_excel(category_id=category_id)
