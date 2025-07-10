# src/main_product.py

import json
import math
from pathlib import Path

from bs4 import BeautifulSoup
from category_manager import category_manager
from config_utils import load_config
from logger import logger
from main_bd import (
    get_all_data_ukrainian_headers,
    get_all_rozetka_data_ukrainian_headers,
    get_product_data,
    get_product_data_rozetka,
    update_prices_and_images,
)
from path_manager import get_path, is_initialized, select_category_and_init_paths
from rozetka_path_manager import get_rozetka_path

# Базовая директория
BASE_DIR = Path(__file__).parent.parent
config = load_config()


# def process_price_data(data):
#     """Обработка данных из файла с ценами"""
#     # logger.info("Обработка цен")
#     try:
#         # # Если данные представлены как список (из файла), берем первый элемент
#         # if isinstance(data, list):
#         #     data = data[0] if data else {}

#         # Получаем объект response из структуры данных
#         json_data = data.get("response", {}).get("data", {})
#         if not json_data:
#             logger.error("В данных отсутствует ключ 'response'")
#             return None

#         # Получаем данные о продукте
#         product_data = json_data.get("wickedProductNoCache", {})
#         if not product_data:
#             logger.error("Не удалось найти данные о продукте")
#             return None
#         # Получаем список аукционов
#         auctions = product_data.get("auctions", {}).get("edges", [])
#         if not auctions:
#             logger.warning("Список аукционов пуст")

#             # Попробуем получить цену из preferredAuction, если он есть
#             preferred_auction = product_data.get("preferredAuction", {})
#             if preferred_auction:
#                 price = preferred_auction.get("price", {}).get("amount")
#                 if price:
#                     logger.info(f"Получена цена из preferredAuction: {price/100} UAH")
#                     return price / 100  # Цена в копейках, делим на 100
#             return None

#         # Собираем все цены из аукционов
#         all_prices = []
#         for edge in auctions:
#             node = edge.get("node", {})
#             price = node.get("price", {}).get("amount")
#             if price:
#                 # Цена в копейках, делим на 100 для получения гривен
#                 all_prices.append(price / 100)
#                 # logger.debug(f"Найдена цена: {price/100} UAH")
#         if not all_prices:
#             logger.warning("Не найдено ни одной цены в аукционах")
#             return None

#         min_price = min(all_prices)
#         # logger.info(f"Минимальная цена: {min_price} UAH")
#         return min_price

#     except Exception as e:
#         logger.error(f"Ошибка при обработке цен: {str(e)}")
#         return None


# Рабочий код
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


def parse_json_and_html_files(category_id):
    """Обрабатывает JSON и HTML файлы для текущей категории на основе slug из БД"""
    # Получаем пути для текущей категории
    slugs_data = get_product_data(category_id=category_id)

    # Извлекаем product_slug из каждого словаря
    slugs = [item["product_slug"] for item in slugs_data if "product_slug" in item]
    
    html_product = get_path("html_product")
    json_dir = get_path("json_dir")
    bd_json = get_path("bd_json")
    output_path = get_path("output_xlsx")

    logger.info(f"Обрабатываем данные для категории: {category_id}")
    logger.info(f"Получено {len(slugs)} slug из БД")
    logger.info(f"Ищем JSON файлы в: {json_dir}")
    logger.info(f"Ищем HTML файлы в: {html_product}")

    all_data = []

    # Создаем индексы для быстрого поиска файлов
    json_files_dict = {}
    html_files_dict = {}

    # Индексируем JSON файлы
    json_files = list(json_dir.glob("*_price.json"))
    for json_file in json_files:
        filename = json_file.stem
        parts = filename.split("_")
        if len(parts) >= 2 and parts[-1] == "price":
            slug = "_".join(parts[:-1])
            json_files_dict[slug] = json_file

    # Индексируем HTML файлы
    html_files = list(html_product.glob("*.html"))
    for html_file in html_files:
        slug = html_file.stem
        html_files_dict[slug] = html_file
        # Также добавляем вариант с заменой символов
        slug_alt = slug.replace("_", "-")
        if slug_alt != slug:
            html_files_dict[slug_alt] = html_file

    logger.info(f"Найдено {len(json_files)} JSON файлов")
    logger.info(f"Найдено {len(html_files)} HTML файлов")
    # Проверяем, есть ли хотя бы какие-то файлы для обработки
    if not json_files and not html_files:
        logger.warning("Не найдено ни JSON, ни HTML файлов для обработки")
        # Создаем пустые записи для всех slug из БД
        for slug in slugs:
            result = {"slug": slug, "price": "нет", "images": []}
            all_data.append(result)

        # Сохраняем пустые данные
        with open(bd_json, "w", encoding="utf-8") as out_file:
            json.dump(all_data, out_file, ensure_ascii=False, indent=4)

        logger.info(f"Созданы пустые записи для {len(all_data)} товаров")
        return all_data, bd_json
    # Обрабатываем каждый slug из БД
    for slug in slugs:
        logger.debug(f"Обрабатываем slug: {slug}")

        result = {"slug": slug, "price": "нет", "images": []}
        if json_files:
            # Обрабатываем JSON файл (цена)
            json_file = json_files_dict.get(slug)
            if json_file:
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data_json = json.load(f)

                    # Извлекаем цену
                    price = process_price_data(data_json)
                    if not price:
                        price = None
                    price_uah_float = float(price)
                    price_uah_rounded = math.ceil(price_uah_float)
                    price_uah = str(price_uah_rounded).replace(".", ",")
                    result["price"] = price_uah

                    logger.debug(f"Найден JSON для {slug}: цена={price_uah}")

                except Exception as e:
                    logger.error(f"Ошибка при чтении JSON файла {json_file}: {str(e)}")
                    result["price"] = "0"
            else:
                logger.debug(f"JSON файл для {slug} не найден")
        else:
            logger.debug("JSON файлы отсутствуют - пропускаем обработку цен")
        if html_files:
            # Обрабатываем HTML файл (изображения)
            html_file = None

            # Ищем HTML файл по разным вариантам slug
            potential_slugs = [
                slug,
                slug.replace("-", "_"),
                slug.replace("_", "-"),
                slug.replace("/", "_"),
            ]

            for potential_slug in potential_slugs:
                if potential_slug in html_files_dict:
                    html_file = html_files_dict[potential_slug]
                    break

            if html_file and html_file.exists():
                try:
                    # Извлекаем данные Apollo State из HTML-файла
                    apollo_data = scrap_html(html_file)

                    if apollo_data:
                        # Извлекаем URL-адреса изображений
                        image_urls = extract_media_urls(apollo_data)
                        if image_urls:
                            result["images"] = image_urls
                            logger.debug(
                                f"Найден HTML для {slug}: изображений={len(image_urls)}"
                            )
                        else:
                            logger.debug(
                                f"HTML файл {html_file} не содержит изображений"
                            )
                    else:
                        logger.warning(
                            f"Не удалось извлечь данные Apollo State из {html_file}"
                        )

                except Exception as e:
                    logger.error(
                        f"Ошибка при обработке HTML файла {html_file}: {str(e)}"
                    )
            else:
                logger.debug(f"HTML файл для {slug} не найден")
        else:
            logger.debug("HTML файлы отсутствуют - пропускаем обработку изображений")
        if not result["images"]:
            result["images"] = []

        all_data.append(result)

        # Логируем результат обработки
        price_status = "✓" if result["price"] != "0" else "✗"
        images_status = "✓" if result["images"] else "✗"
        logger.info(
            f"Обработан {slug}: цена={price_status}, изображения={images_status}"
        )

    # Сохраняем все данные в JSON-файл
    with open(bd_json, "w", encoding="utf-8") as out_file:
        json.dump(all_data, out_file, ensure_ascii=False, indent=4)

    # Статистика обработки
    items_with_price = sum(1 for item in all_data if item["price"] != "0")
    items_with_images = sum(1 for item in all_data if item["images"])
    items_complete = sum(
        1 for item in all_data if item["price"] != "0" and item["images"]
    )

    logger.info(f"Данные сохранены в {bd_json}")
    logger.info(f"Всего slug из БД: {len(slugs)}")
    logger.info(f"Обработано товаров: {len(all_data)}")
    logger.info(f"Товаров с ценой: {items_with_price}")
    logger.info(f"Товаров с изображениями: {items_with_images}")
    logger.info(f"Полных товаров (цена + изображения): {items_complete}")

    return all_data, bd_json


# def parse_json_and_html_files_rozetka():
#     """Обрабатывает JSON и HTML файлы для текущей категории"""
#     # Получаем пути для текущей категории
#     html_product = get_rozetka_path("html_product")
#     json_dir = get_rozetka_path("json_dir")
#     bd_json = get_rozetka_path("bd_json")
#     output_path = get_rozetka_path("output_xlsx")
#     category_id = get_rozetka_path("category_id")

#     logger.info(f"Обрабатываем данные Rozetka для категории: {category_id}")

#     all_data = []
#     json_files = list(json_dir.glob("*_price.json"))
#     html_files = list(html_product.glob("*.html"))
#     logger.info(len(json_files))
#     logger.info(len(html_files))
#     exit()
#     logger.info(f"Найдено {len(json_files)} JSON файлов для обработки")
#     logger.info(json_dir)

#     for json_file in json_files:
#         filename = json_file.stem
#         parts = filename.split("_")
#         if len(parts) < 2 or parts[-1] != "price":
#             logger.warning(f"Некорректное имя файла: {filename}, пропускаем")
#             continue

#         slug = "_".join(parts[:-1])
#         logger.info(json_file)
#         try:
#             with open(json_file, "r", encoding="utf-8") as f:
#                 data_json = json.load(f)
#         except Exception as e:
#             logger.error(f"Ошибка при чтении файла {json_file}: {str(e)}")
#             continue

#         # Извлекаем цену
#         price = process_price_data(data_json)
#         if not price:
#             price = 0
#         price_uah_float = float(price)
#         price_uah_rounded = math.ceil(price_uah_float)
#         price_uah = str(price_uah_rounded).replace(".", ",")

#         # Ищем соответствующий HTML-файл по slug
#         html_file = html_product / f"{slug}.html"
#         if not html_file.exists():
#             html_file = html_product / f"{slug.replace('-', '_')}.html"
#             if not html_file.exists():
#                 logger.warning(f"HTML-файл {html_file} не найден")
#                 result = {"slug": slug, "price": price_uah, "images": []}
#                 all_data.append(result)
#                 continue

#         # Извлекаем данные Apollo State из HTML-файла
#         apollo_data = scrap_html(html_file)

#         if not apollo_data:
#             logger.error(f"Не удалось извлечь данные Apollo State из {html_file}")
#             result = {"slug": slug, "price": price_uah, "images": []}
#             all_data.append(result)
#             continue

#         # Извлекаем URL-адреса изображений
#         image_urls = extract_media_urls(apollo_data)
#         if not image_urls:
#             image_urls = []

#         # Формируем результат с ценой и URL-адресами изображений
#         result = {"slug": slug, "price": price_uah, "images": image_urls}
#         all_data.append(result)

#     # Сохраняем все данные в JSON-файл
#     with open(bd_json, "w", encoding="utf-8") as out_file:
#         json.dump(all_data, out_file, ensure_ascii=False, indent=4)

#     logger.info(
#         f"Данные сохранены в {bd_json}, всего обработано {len(all_data)} товаров"
#     )
#     logger.info(f"Все данные будут привязаны к категории: {category_id}")


#     return all_data, bd_json
def parse_json_and_html_files_rozetka(category_id):
    """Обрабатывает JSON и HTML файлы для текущей категории на основе slug из БД"""
    # Получаем пути для текущей категории
    # category_id = get_rozetka_path("category_id")
    slugs_data = get_product_data_rozetka(category_id=category_id)

    # Извлекаем product_slug из каждого словаря
    slugs = [item["product_slug"] for item in slugs_data if "product_slug" in item]

    html_product = get_rozetka_path("html_product")
    json_dir = get_rozetka_path("json_dir")
    bd_json = get_rozetka_path("bd_json")
    output_path = get_rozetka_path("output_xlsx")

    logger.info(f"Обрабатываем данные для категории: {category_id}")
    logger.info(f"Получено {len(slugs)} slug из БД")
    logger.info(f"Ищем JSON файлы в: {json_dir}")
    logger.info(f"Ищем HTML файлы в: {html_product}")

    all_data = []

    # Создаем индексы для быстрого поиска файлов
    json_files_dict = {}
    html_files_dict = {}

    # Индексируем JSON файлы
    json_files = []
    if json_dir and json_dir.exists():
        json_files = list(json_dir.glob("*_price.json"))
        for json_file in json_files:
            filename = json_file.stem
            parts = filename.split("_")
            if len(parts) >= 2 and parts[-1] == "price":
                slug = "_".join(parts[:-1])
                json_files_dict[slug] = json_file
    else:
        logger.warning(f"Папка JSON не найдена или не существует: {json_dir}")

    # Индексируем HTML файлы
    html_files = []
    if html_product and html_product.exists():
        html_files = list(html_product.glob("*.html"))
        for html_file in html_files:
            slug = html_file.stem
            html_files_dict[slug] = html_file
            # Также добавляем вариант с заменой символов
            slug_alt = slug.replace("_", "-")
            if slug_alt != slug:
                html_files_dict[slug_alt] = html_file
    else:
        logger.warning(f"Папка HTML не найдена или не существует: {html_product}")

    logger.info(f"Найдено {len(json_files)} JSON файлов")
    logger.info(f"Найдено {len(html_files)} HTML файлов")

    # Проверяем, есть ли хотя бы какие-то файлы для обработки
    if not json_files and not html_files:
        logger.warning("Не найдено ни JSON, ни HTML файлов для обработки")
        # Создаем пустые записи для всех slug из БД
        for slug in slugs:
            result = {"slug": slug, "price": "нет", "images": []}
            all_data.append(result)

        # Сохраняем пустые данные
        with open(bd_json, "w", encoding="utf-8") as out_file:
            json.dump(all_data, out_file, ensure_ascii=False, indent=4)

        logger.info(f"Созданы пустые записи для {len(all_data)} товаров")
        return all_data, bd_json

    # Обрабатываем каждый slug из БД
    for slug in slugs:
        logger.debug(f"Обрабатываем slug: {slug}")

        result = {"slug": slug, "price": "нет", "images": []}
        if json_files:
            # Обрабатываем JSON файл (цена)
            json_file = json_files_dict.get(slug)
            # logger.info("Почемы тут если файлов нету")
            # logger.info(json_file)
            if json_file:
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data_json = json.load(f)

                    # Извлекаем цену
                    price = process_price_data(data_json)
                    if price:  # Только если цена есть
                        price_uah_float = float(price)
                        price_uah_rounded = math.ceil(price_uah_float)
                        price_uah = str(price_uah_rounded).replace(".", ",")
                        result["price"] = price_uah

                    logger.debug(f"Найден JSON для {slug}: цена={price_uah}")

                except Exception as e:
                    logger.error(f"Ошибка при чтении JSON файла {json_file}: {str(e)}")
                    result["price"] = "0"
            else:
                logger.debug(f"JSON файл для {slug} не найден")
        else:
            logger.debug("JSON файлы отсутствуют - пропускаем обработку цен")
        if html_files:
            # Обрабатываем HTML файл (изображения)
            html_file = None

            # Ищем HTML файл по разным вариантам slug
            potential_slugs = [
                slug,
                slug.replace("-", "_"),
                slug.replace("_", "-"),
                slug.replace("/", "_"),
            ]

            for potential_slug in potential_slugs:
                if potential_slug in html_files_dict:
                    html_file = html_files_dict[potential_slug]
                    break

            if html_file and html_file.exists():
                try:
                    # Извлекаем данные Apollo State из HTML-файла
                    apollo_data = scrap_html(html_file)

                    if apollo_data:
                        # Извлекаем URL-адреса изображений
                        image_urls = extract_media_urls(apollo_data)
                        if image_urls:
                            result["images"] = image_urls
                            logger.debug(
                                f"Найден HTML для {slug}: изображений={len(image_urls)}"
                            )
                        else:
                            logger.debug(
                                f"HTML файл {html_file} не содержит изображений"
                            )
                    else:
                        logger.warning(
                            f"Не удалось извлечь данные Apollo State из {html_file}"
                        )

                except Exception as e:
                    logger.error(
                        f"Ошибка при обработке HTML файла {html_file}: {str(e)}"
                    )
            else:
                logger.debug(f"HTML файл для {slug} не найден")
        else:
            logger.debug("HTML файлы отсутствуют - пропускаем обработку изображений")
        if not result["images"]:
            result["images"] = []

        all_data.append(result)

        # Логируем результат обработки
        price_status = "✓" if result["price"] not in ["0", None] else "✗"
        images_status = "✓" if result["images"] else "✗"
        logger.info(
            f"Обработан {slug}: цена={price_status}, изображения={images_status}"
        )

    # Сохраняем все данные в JSON-файл
    with open(bd_json, "w", encoding="utf-8") as out_file:
        json.dump(all_data, out_file, ensure_ascii=False, indent=4)

    # Статистика обработки
    items_with_price = sum(1 for item in all_data if item["price"] not in ["0", None])
    items_with_images = sum(1 for item in all_data if item["images"])
    items_complete = sum(
        1 for item in all_data if item["price"] not in ["0", None] and item["images"]
    )

    logger.info(f"Данные сохранены в {bd_json}")
    logger.info(f"Всего slug из БД: {len(slugs)}")
    logger.info(f"Обработано товаров: {len(all_data)}")
    logger.info(f"Товаров с ценой: {items_with_price}")
    logger.info(f"Товаров с изображениями: {items_with_images}")
    logger.info(f"Полных товаров (цена + изображения): {items_complete}")

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


def save_to_excel_rozetka(data, output_path):
    """
    Сохраняет данные в Excel файл

    Args:
        data (list): Список словарей с данными
        output_path (str or Path): Путь для сохранения Excel файла

    Returns:
        bool: True, если сохранение успешно, иначе False
    """
    html_product = get_rozetka_path("html_product")
    json_dir = get_rozetka_path("json_dir")
    bd_json = get_rozetka_path("bd_json")
    output_path = get_rozetka_path("output_xlsx")
    category_id = get_rozetka_path("category_id")
    try:
        import pandas as pd

        # Создаем DataFrame из списка словарей
        df = pd.DataFrame(data)

        # Сохраняем в Excel
        df.to_excel(output_path, index=False)

        # logger.info(f"Данные успешно сохранены в {output_path}")
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


def remove_keys_from_dicts_list(dicts_list, keys_to_remove):
    """
    Удаляет указанные ключи из списка словарей
    """
    return [remove_keys_from_dict(d, keys_to_remove) for d in dicts_list]


def remove_keys_from_dict(dictionary, keys_to_remove):
    """
    Удаляет указанные ключи из словаря
    """
    return {k: v for k, v in dictionary.items() if k not in keys_to_remove}


def clear_keys_in_dicts_list(dicts_list, keys_to_clear, default_value=""):
    """
    Очищает значения указанных ключей в списке словарей, но оставляет сами ключи

    Args:
        dicts_list (list): Список словарей
        keys_to_clear (list): Список ключей для очистки значений
        default_value: Значение по умолчанию для очищенных ключей (по умолчанию пустая строка)

    Returns:
        list: Список словарей с очищенными значениями
    """
    return [clear_keys_in_dict(d, keys_to_clear, default_value) for d in dicts_list]


def clear_keys_in_dict(dictionary, keys_to_clear, default_value=""):
    """
    Очищает значения указанных ключей в словаре, но оставляет сами ключи

    Args:
        dictionary (dict): Словарь для обработки
        keys_to_clear (list): Список ключей для очистки значений
        default_value: Значение по умолчанию для очищенных ключей

    Returns:
        dict: Словарь с очищенными значениями
    """
    result = dictionary.copy()  # Создаем копию словаря

    for key in keys_to_clear:
        if key in result:
            result[key] = default_value

    return result


def export_data_to_excel_rozetka(category_id=None):
    """
    Экспортирует данные из базы в Excel файл

    Args:
        category_id (str, optional): ID категории для фильтрации
    """
    # ИСПРАВЛЕНИЕ: Передаем category_id в функцию получения данных
    data = get_all_rozetka_data_ukrainian_headers(category_id=category_id)

    html_product = get_rozetka_path("html_product")
    json_dir = get_rozetka_path("json_dir")
    bd_json = get_rozetka_path("bd_json")
    output_path = get_rozetka_path("output_xlsx")
    current_category_id = get_rozetka_path("category_id")

    # ИСПРАВЛЕНИЕ: Логируем информацию о фильтрации
    if category_id:
        logger.info(f"Экспортируем данные Rozetka для категории: {category_id}")
    else:
        logger.info("Экспортируем все данные Rozetka (без фильтрации по категории)")

    if data:
        data_without_slug = remove_keys_from_dicts_list(data, ["product_slug"])
        data_without_slug = clear_keys_in_dicts_list(data_without_slug, ["CID"])
        # Сохраняем данные в Excel
        success = save_to_excel_rozetka(data_without_slug, output_path)

        # if success:
        #     # logger.info(f"Данные успешно экспортированы в {output_path}")
        #     # logger.info(f"Экспортировано записей: {len(data_without_slug)}")
        # else:
        #     logger.error("Не удалось экспортировать данные в Excel")
    else:
        logger.warning("Нет данных для экспорта")
        if category_id:
            logger.warning(f"Возможно, в категории {category_id} нет данных")


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


# if __name__ == "__main__":
#     # Инициализация категории
#     category_info = select_category_and_init_paths()

#     category_id = get_path("category_id")
#     if not category_info:
#         logger.error("Не удалось инициализировать категорию")
#         exit(1)

#     # Собираем данные из JSON и HTML файлов
#     all_data, bd_json_path = parse_json_and_html_files()

#     if not all_data:
#         logger.warning("Нет данных для обновления")
#         exit(0)

#     # Обновляем данные в БД
#     updated_prices, updated_images, errors = update_prices_and_images(
#         bd_json_path, category_id=category_id
#     )

#     logger.info(f"Обновление данных завершено:")
#     logger.info(f"- Обновлено цен: {updated_prices}")
#     logger.info(f"- Обновлено изображений: {updated_images}")
#     logger.info(f"- Ошибок: {errors}")

#     # Экспортируем в Excel для выбранной категории
#     export_data_to_excel(category_id=category_id)
