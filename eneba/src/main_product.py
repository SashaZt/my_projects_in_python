# src/main_product.py

import json
import math
from pathlib import Path

from bs4 import BeautifulSoup
from config_utils import load_config
from logger import logger
from main_bd import get_all_data_ukrainian_headers, update_prices_and_images

# Пути и директории

BASE_DIR = Path(__file__).parent.parent
config = load_config()

# Получаем параметры из конфигурации
html_product = BASE_DIR / config["directories"]["html_product"]
output_path = BASE_DIR / config["files"]["output_xlsx"]
bd_json = BASE_DIR / config["files"]["bd_json"]
temp_json = BASE_DIR / config["files"]["temp_json"]
json_dir = BASE_DIR / config["directories"]["json"]


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
    all_data = []
    for json_file in json_dir.glob("*.json"):
        filename = json_file.stem
        logger.debug(f"Обрабатываем файл: {filename}")

        # Разделяем имя файла по '_'
        parts = filename.split("_")
        if len(parts) < 2:
            logger.warning(f"Некорректное имя файла: {filename}, пропускаем")
            continue

        slug = "_".join(parts[:-1])

        # Открываем файл и загружаем данные
        with open(json_file, "r", encoding="utf-8") as f:
            data_json = json.load(f)

        # Извлекаем цену
        price = process_price_data(data_json)
        # Преобразуем строку в число с плавающей точкой
        if not price:
            price = 0
        price_uah_float = float(price)
        # Округляем в большую сторону до целого
        price_uah_rounded = math.ceil(price_uah_float)
        price_uah = str(price_uah_rounded).replace(".", ",")
        # Ищем соответствующий HTML-файл по slug
        # Пробуем несколько вариантов имени файла
        possible_html_files = [
            html_product / f"{slug}.html",
            html_product / f"{slug.replace('/', '_')}.html",
            # Можно добавить другие варианты поиска файла при необходимости
        ]

        html_file_found = None
        for possible_file in possible_html_files:
            if possible_file.exists():
                html_file_found = possible_file
                break

        image_urls = None
        if html_file_found:
            logger.debug(f"Найден HTML-файл {html_file_found.name} для {slug}")
            # Извлекаем данные Apollo State из HTML-файла
            apollo_data = scrap_html(html_file_found)

            if apollo_data:
                # Извлекаем URL-адреса изображений
                image_urls = extract_media_urls(apollo_data)
                logger.debug(f"Извлечено {len(image_urls)} изображений для {slug}")
            else:
                logger.error(
                    f"Не удалось извлечь данные Apollo State из {html_file_found}"
                )
        else:
            logger.warning(f"HTML-файл для {slug} не найден")

        # Формируем результат с ценой и URL-адресами изображений
        result = {"slug": slug, "price": price_uah, "images": image_urls}
        all_data.append(result)
        logger.info(f"Обработан {slug}: цена={price}, изображений={len(image_urls)}")

    # Сохраняем все данные в JSON-файл
    with open(bd_json, "w", encoding="utf-8") as out_file:
        json.dump(all_data, out_file, ensure_ascii=False, indent=4)

    logger.info(
        f"Данные сохранены в {bd_json}, всего обработано {len(all_data)} товаров"
    )
    return all_data


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


def export_data_to_excel():
    """
    Экспортирует данные из базы в Excel файл
    """
    # Получаем данные из базы с украинскими заголовками
    data = get_all_data_ukrainian_headers()

    if data:
        # Определяем путь к выходному файлу

        # Сохраняем данные в Excel
        success = save_to_excel(data, output_path)

        if success:
            logger.info(f"Данные успешно экспортированы в {output_path}")
        else:
            logger.error("Не удалось экспортировать данные в Excel")
    else:
        logger.warning("Нет данных для экспорта")


if __name__ == "__main__":
    # Собираем данные с json и html
    parse_json_and_html_files()
    # Обновляем данные в бд
    update_prices_and_images(bd_json)
    # Експортируем в ексель
    export_data_to_excel()
