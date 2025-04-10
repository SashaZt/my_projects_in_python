# src/main_page.py
# Рабочий, до категории добавка
import json
import math
import os
import random
import re
import shutil
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from category_manager import category_manager
from config_utils import load_config
from loguru import logger
from main_bd import load_and_save_data

BASE_URL = "https://www.eneba.com/"
# Базовая директория — текущая рабочая директория
BASE_DIR = Path(__file__).parent.parent
config = load_config()

# Получаем параметры из конфигурации
url = config["site"]["url"]
start_page = int(config["site"]["start"])
num_pages = int(config["site"]["pages"])
delay = int(config["site"]["delay"])
cookies = config["cookies"]
headers = config["headers"]
output_json = BASE_DIR / config["files"]["output_json"]
output_xlsx = BASE_DIR / config["files"]["output_xlsx"]
new_output_xlsx = BASE_DIR / config["files"]["new_output_xlsx"]
html_page = BASE_DIR / config["directories"]["html_page"]


def build_url_for_page(base_url, page_number):
    """
    Собирает URL для конкретной страницы

    Args:
        base_url (str): Базовый URL
        page_number (int): Номер страницы

    Returns:
        str: URL с параметром page для заданной страницы
    """
    parsed_url = urlparse(base_url)

    # Получаем параметры из URL
    params = parse_qs(parsed_url.query)

    # Обновляем параметр page
    params["page"] = [str(page_number)]

    # Собираем URL с обновленными параметрами
    new_query = urlencode(params, doseq=True)

    # Собираем новый URL
    url_parts = list(parsed_url)
    url_parts[4] = new_query

    return urlunparse(url_parts)


def get_html(url, output_file, cookies, headers, delay=2):
    """
    Загружает HTML-страницу по указанному URL и сохраняет в файл

    Args:
        url (str): URL для загрузки
        output_file (Path): Путь для сохранения HTML
        cookies (dict): Куки для запроса
        headers (dict): Заголовки для запроса
        delay (int): Задержка в секундах перед запросом (для избежания блокировки)

    Returns:
        bool: True, если загрузка успешна, иначе False
    """
    # Небольшая задержка перед запросом для избежания блокировки
    time.sleep(delay)

    try:
        logger.info(f"Загрузка страницы: {url}")
        response = requests.get(
            url,
            cookies=cookies,
            headers=headers,
            timeout=30,
        )

        # Проверка кода ответа
        if response.status_code == 200:
            # Сохранение HTML-страницы целиком
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(response.text)
            logger.info(f"Успешно сохранен {output_file}")
            return True
        else:
            logger.error(
                f"Не удалось получить HTML. Код ответа: {response.status_code}"
            )
            return False
    except Exception as e:
        logger.error(f"Ошибка при получении HTML: {str(e)}")
        return False


def scrap_html(html_file, output_json_file=None):
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
                # Сохранение данных в JSON-файл если указан путь
                if output_json_file:
                    with open(output_json_file, "w", encoding="utf-8") as out_file:
                        json.dump(data_dict, out_file, ensure_ascii=False, indent=4)
                    logger.info(
                        f"Данные Apollo State успешно сохранены в {output_json_file}"
                    )
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


def clean_product_name(product_name, max_length=24):
    """
    Очищает product_name от спецсимволов, заменяя их на подчеркивание,
    и ограничивает длину строки
    """
    # Берем первые max_length символов
    truncated = product_name[:max_length] if product_name else ""

    # Заменяем спецсимволы на подчеркивание
    cleaned = re.sub(r"[^\w\s]", "_", truncated)

    # Заменяем пробелы на подчеркивание и убираем повторяющиеся подчеркивания
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)

    return cleaned


def process_apollo_data(apollo_data):
    """
    Обрабатывает данные Apollo State и формирует список товаров
    в требуемом формате

    Args:
        apollo_data (dict): Данные Apollo State

    Returns:
        list: Список товаров
    """
    result = []
    all_slugs = set()
    # Словари для хранения информации об аукционах и продуктах
    auctions = {}
    products = {}

    # Сначала собираем все данные аукционов и продуктов
    for key, value in apollo_data.items():
        if key.startswith("Auction::"):
            auctions[key] = value
        elif key.startswith("Product::"):
            products[key] = value

    # Для каждого продукта находим соответствующий аукцион и формируем запись
    for product_key, product in products.items():

        # Проверяем, есть ли у продукта ссылка на аукцион
        cheapest_auction = product.get("cheapestAuction", {})
        if not cheapest_auction:
            continue
        cheapest_auction_ref = cheapest_auction.get("__ref")

        if not cheapest_auction_ref:
            continue

        # Получаем данные аукциона
        auction = auctions.get(cheapest_auction_ref)
        if not auction:
            continue

        # Получаем цену в UAH и делим на 100
        price_uah = None
        price_data = auction.get('price({"currency":"UAH"})')
        if price_data and "amount" in price_data:
            price_uah_str = str(
                price_data["amount"] / 100
            )  # Получаем строку, например "50.35"
            if price_uah_str:
                price_uah_float = float(
                    price_uah_str
                )  # Преобразуем строку в число с плавающей точкой
                price_uah_rounded = math.ceil(
                    price_uah_float
                )  # Округляем в большую сторону до целого
                price_uah = str(price_uah_rounded).replace(
                    ".", ","
                )  # Преобразуем обратно в строку и меняем точку на запятую
            else:
                price_uah = None

        # Получаем имя продукта
        product_name = product.get("name", "")

        if product_name:
            # Удаляем "XBOX LIVE Key" из названия
            product_name = (
                product_name.replace("XBOX LIVE Key", "")
                .replace("Xbox Live Key", "")
                .strip()
            )
            # Получаем регионы из продукта
            regions = []

            if "regions" in product and isinstance(product["regions"], list):
                for region in product["regions"]:
                    if isinstance(region, dict) and "name" in region:
                        # Добавляем название региона и его вариант в верхнем регистре
                        regions.append(region["name"].upper())

            # Удаляем название региона из конца наименования товара
            for region in regions:
                # Проверяем наличие региона в конце строки (с учетом возможного пробела)
                if product_name.endswith(region):
                    product_name = product_name[: -len(region)].strip()
                elif product_name.endswith(" " + region):
                    product_name = product_name[: -(len(region) + 1)].strip()

        # Получаем slug продукта
        product_slug_str = product.get("slug", "")
        # Получаем URL изображения
        img_url = ""
        cover_data = product.get('cover({"size":300})')
        if cover_data and "src" in cover_data:
            img_url = cover_data["src"]
        cleaned_name = clean_product_name(
            product_name
        )  # Результат: "Product_Name_Special"
        # Формируем запись согласно требуемым заголовкам
        item = {
            "product_slug": product_slug_str,
            "Код_товару": cleaned_name,
            "Назва_позиції": f"{product_name} Код для Xbox One/Series S|X",
            "Назва_позиції_укр": f"{product_name} Код для Xbox One/Series S|X",
            "Пошукові_запити": f"{product_name},Xbox,xbox ігри,xbox game pass ultimate активация,xbox game pass для консолей,подписка xbox game pass пк,xbox game pass ultimate,xbox game pass 1 месяц,xbox game pass ultimate 5 месяцев,xbox game pass ultimate 5 місяців,xbox game pass ultimate 9 місяців,xbox game pass ultimate 25 місяців,xbox game pass ultimate 13 місяців,xbox game pass ultimate 17 місяців,xbox game pass ultimate продление,подписка xbox game pass ultimate 1 месяц,подписка xbox game pass ultimate 5 месяцев,подписка xbox game pass ultimate 9 месяцев,подписка xbox game pass ultimate 24 месяца,подписка xbox game pass ultimate 13 месяцев,подписка xbox game pass ultimate 17 месяцев,підписка xbox game pass ultimate 5 місяців,підписка xbox game pass ultimate 9 місяців,підписка xbox game pass ultimate 24 місяці,підписка xbox game pass ultimate 13 місяців,підписка xbox game pass ultimate 12 місяців,підписка xbox game pass ultimate 17 місяців,",
            "Пошукові_запити_укр": f"{product_name},Xbox,xbox ігри,xbox game pass ultimate активация,xbox game pass для консолей,подписка xbox game pass пк,xbox game pass ultimate,xbox game pass 1 месяц,xbox game pass ultimate 5 месяцев,xbox game pass ultimate 5 місяців,xbox game pass ultimate 9 місяців,xbox game pass ultimate 25 місяців,xbox game pass ultimate 13 місяців,xbox game pass ultimate 17 місяців,xbox game pass ultimate продление,подписка xbox game pass ultimate 1 месяц,подписка xbox game pass ultimate 5 месяцев,подписка xbox game pass ultimate 9 месяцев,подписка xbox game pass ultimate 24 месяца,подписка xbox game pass ultimate 13 месяцев,подписка xbox game pass ultimate 17 месяцев,підписка xbox game pass ultimate 5 місяців,підписка xbox game pass ultimate 9 місяців,підписка xbox game pass ultimate 24 місяці,підписка xbox game pass ultimate 13 місяців,підписка xbox game pass ultimate 12 місяців,підписка xbox game pass ultimate 17 місяців,",
            "Опис": f"<p><strong>Добро пожаловать в наш магазин цифровых товаров &laquo;XGames_Store&raquo; у нас лучшие цены и предложения!!!</strong></p><p><strong>Пожалуйста, внимательно ознакомьтесь с описанием перед покупкой.</strong></p><p><strong>Вы получите лицензионный цифровой код для активации игры {product_name}!</strong></p><p><strong>Доставка осуществляется только по полной предоплате.<br />Доставка цифрового товара через Telegram/Viber/Whatsapp/Email !!!</strong></p><p><strong>Игра активируется навсегда на вашем аккаунте Microsoft !</strong></p><p><strong>Предоставляем инструкцию и помогаем с активацией (Во время активации может понадобиться VPN или изменение региона / страны).<br /><br />В наличии более 1000 игр для консолей XBOX!</strong></p>",
            "Опис_укр": f"<p><strong>Ласкаво просимо до нашого магазину цифрових товарів &quot;XGames_Store&quot; у нас найкращі ціни та пропозиції!!</strong></p><p><strong>Будь ласка, уважно ознайомтесь з описом перед покупкою.</strong></p><p><strong>Ви отримаєте ліцензійний цифровий код для активації гри {product_name}!</strong></p><p><strong>Доставка здійснюється тільки за повною передоплатою.<br />Доставка цифрового товару через Telegram/Viber/Whatsapp/Email !!!</strong></p><p><strong>Гра активується назавжди на вашому акаунті Microsoft !</strong></p><p><strong>Надаємо інструкцію та допомагаємо з активацією (Під час активації може знадобитись VPN або зміна регіону/країни).<br /><br />В наявності більше 1000 ігор для консолей XBOX!</strong></p>",
            "Тип_товару": "r",
            "Ціна": price_uah,
            "Валюта": "UAH",
            "Одиниця_виміру": "шт.",
            "Мінімальний_обсяг_замовлення": None,
            "Оптова_ціна": None,
            "Мінімальне_замовлення_опт": None,
            "Посилання_зображення": img_url,
            "Наявність": "!",
            "Кількість": None,
            "Номер_групи": "129793815",
            "Назва_групи": "Игры для Xbox",
            "Посилання_підрозділу": "https://prom.ua/Video-igry",
            "Можливість_поставки": None,
            "Термін_поставки": None,
            "Спосіб_пакування": None,
            "Спосіб_пакування_укр": None,
            "Унікальний_ідентифікатор": None,
            "Ідентифікатор_товару": None,
            "Ідентифікатор_підрозділу": "180606",
            "Ідентифікатор_групи": None,
            "Виробник": "Microsoft",
            "Країна_виробник": "США",
            "Знижка": "5%",
            "ID_групи_різновидів": None,
            "Особисті_нотатки": None,
            "Продукт_на_сайті": None,
            "Термін_дії_знижки_від": None,
            "Термін_дії_знижки_до": None,
            "Ціна_від": "-",
            "Ярлик": "Топ",
            "HTML_заголовок": None,
            "HTML_заголовок_укр": None,
            "HTML_опис": None,
            "HTML_опис_укр": None,
            "Код_маркування_(GTIN)": None,
            "Номер_пристрою_(MPN)": None,
            "Вага,кг": None,
            "Ширина,см": None,
            "Висота,см": None,
            "Довжина,см": None,
            "Де_знаходиться_товар": None,
            "Назва_Характеристики": "Платформа",
            "Одиниця_виміру_Характеристики": None,
            "Значення_Характеристики": "Xbox Series X",
        }

        result.append(item)

    return result, all_slugs


def save_products_to_excel(all_products, output_file):
    """
    Преобразует список товаров в DataFrame, удаляет дубли и сохраняет в Excel

    Args:
        all_products (list): Список словарей с товарами
        output_file (str): Путь для сохранения результата

    Returns:
        pandas.DataFrame: Обработанный DataFrame с товарами
    """
    if not all_products:
        logger.error("Не найдено товаров для сохранения")
        return None

    # Создаем DataFrame
    df = pd.DataFrame(all_products)
    logger.info(f"Создан DataFrame из {len(df)} товаров")

    # # Удаляем дубли, оставляя позиции с минимальной ценой
    # df_filtered = remove_duplicates_by_price(df)

    # Сохраняем в Excel
    df.to_excel(output_file, index=False)
    logger.info(f"Данные успешно сохранены в {output_file}")

    return df


def download_pages(base_url, start_page, num_pages, cookies, headers, delay):
    """
    Скачивает HTML-страницы с сайта и сохраняет их в директорию html

    Args:
        base_url (str): Базовый URL с фильтрами
        start_page (int): Начальная страница
        num_pages (int): Количество страниц для скачивания
        cookies (dict): Куки для запроса
        headers (dict): Заголовки для запроса
        delay (int): Задержка между запросами в секундах

    Returns:
        int: Количество успешно скачанных страниц
    """
    # Проверяем существующие файлы HTML
    existing_files = []
    page_pattern = re.compile(r"eneba_page_(\d+)\.html")
    for file in html_page.glob("eneba_page_*.html"):
        match = page_pattern.search(file.name)
        if match:
            existing_files.append(int(match.group(1)))

    # Сортируем номера страниц
    existing_files.sort()

    logger.info(f"Найдено существующих HTML-файлов: {len(existing_files)}")

    # Определяем, какие страницы нужно скачать
    pages_to_download = []
    for page in range(start_page, start_page + num_pages):
        if page not in existing_files:
            pages_to_download.append(page)

    logger.info(f"Страниц для скачивания: {len(pages_to_download)}")

    # Если все страницы уже скачаны, возвращаем их количество
    if not pages_to_download:
        logger.info("Все страницы уже скачаны")
        return len(existing_files)

    # Скачиваем недостающие страницы
    successful_downloads = 0

    for page in pages_to_download:
        logger.info(f"Скачивание страницы {page}...")

        # Создаем имя файла для текущей страницы
        page_html_file = html_page / f"eneba_page_{page}.html"

        # Собираем URL для текущей страницы
        page_url = build_url_for_page(base_url, page)
        logger.info(f"URL: {page_url}")

        # Загружаем HTML страницы
        if get_html(page_url, page_html_file, cookies, headers, delay):
            successful_downloads += 1

            # Добавляем случайную задержку между страницами
            if pages_to_download.index(page) < len(pages_to_download) - 1:
                sleep_time = random.randint(delay, delay + 5)
                logger.info(f"Случайная задержка между страницами: {sleep_time} секунд")
                time.sleep(sleep_time)
        else:
            logger.error(f"Не удалось загрузить страницу {page}")

    logger.info(
        f"Скачивание завершено. Успешно скачано страниц: {successful_downloads}"
    )

    # Возвращаем общее количество страниц (существующие + новые)
    return len(existing_files) + successful_downloads


def process_html_files():
    """
    Обрабатывает HTML-файлы в директории html и создает Excel-файл с товарами

    Returns:
        list: Список всех товаров
    """
    logger.info("Начинаем обработку HTML-файлов...")

    all_products = []

    # logger.info(
    #     f"Найдено HTML-файлов для обработки: {len(html_directory.glob("*.html"))}"
    # )
    all_urls = []
    for html_file in html_page.glob("*.html"):
        logger.info(f"Обработка файла: {html_file.name}")

        # Извлекаем данные Apollo State
        apollo_data = scrap_html(html_file)

        if apollo_data:
            # Обрабатываем данные Apollo State
            page_products, urls = process_apollo_data(apollo_data)

            # Добавляем продукты к общему списку
            all_products.extend(page_products)
            all_urls.extend(urls)
            logger.info(f"Извлечено товаров из {html_file.name}: {len(page_products)}")
        else:
            logger.error(
                f"Не удалось извлечь данные Apollo State из файла {html_file.name}"
            )
    # url_data = pd.DataFrame(all_urls, columns=["url"])
    # url_data.to_csv(output_csv_file, index=False)
    # Сохраняем результат в Excel

    if all_products:
        all_products = remove_duplicates_by_price_json(all_products)
        with open(output_json, "w", encoding="utf-8") as json_file:
            json.dump(all_products, json_file, ensure_ascii=False, indent=4)
        data_without_slug = remove_keys_from_dicts_list(all_products, ["product_slug"])
        save_products_to_excel(data_without_slug, output_xlsx)
        load_and_save_data(output_json)
    else:
        logger.error("Не найдено товаров для сохранения")

    return all_products


def remove_duplicates_by_price_json(all_products):
    """
    Удаляет дубли товаров в списке словарей JSON, оставляя только позиции с наименьшей ценой

    Args:
        all_products (list): Список словарей с товарами

    Returns:
        list: Обработанный список словарей без дублей
    """
    # Проверка, что входные данные не пустые
    if not all_products:
        print("Список товаров пуст")
        return all_products

    # Создаем словарь для хранения товаров по их названиям
    products_by_name = {}

    # Вывод исходного количества товаров
    initial_count = len(all_products)
    logger.info(f"Всего товаров до обработки: {initial_count}")

    # Первый проход: группировка товаров по названию
    for product in all_products:
        # Проверяем наличие необходимых ключей
        if "Назва_позиції" not in product or "Ціна" not in product:
            continue

        name = product["Назва_позиції"]
        price_str = product["Ціна"]

        # Преобразуем цену в числовой формат
        try:
            price_num = (
                float(price_str.replace(",", "."))
                if price_str and price_str.strip()
                else float("inf")
            )
        except (ValueError, AttributeError):
            price_num = float("inf")

        # Добавляем информацию о товаре в словарь
        if name not in products_by_name:
            products_by_name[name] = []

        products_by_name[name].append({"product": product, "price_num": price_num})

    # Создаем список для хранения уникальных товаров
    unique_products = []

    # Второй проход: выбираем товары с минимальной ценой
    for name, products in products_by_name.items():
        # Если это не дубль, просто добавляем товар
        if len(products) <= 1:
            unique_products.append(products[0]["product"])
            continue

        # Сортируем товары по цене (от меньшей к большей)
        sorted_products = sorted(products, key=lambda x: x["price_num"])

        # Если есть дубли, логируем информацию
        logger.info(f"Найдены дубли: '{name}'")

        # Добавляем товар с минимальной ценой в список уникальных товаров
        min_price_product = sorted_products[0]["product"]
        unique_products.append(min_price_product)
        logger.info(f"  - ОСТАВЛЕНА: Цена {min_price_product['Ціна']}")

        # Логируем информацию об удаленных товарах
        for product_info in sorted_products[1:]:
            logger.info(f"  - УДАЛЕНА: Цена {product_info['product']['Ціна']}")

    # Выводим итоговую статистику
    removed_count = initial_count - len(unique_products)
    logger.info(f"Удалено дублирующихся позиций: {removed_count}")
    logger.info(f"Всего товаров после обработки: {len(unique_products)}")

    return unique_products


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


def update_prices_from_config():
    """
    Обновляет цены в Excel файле на основе ценовых диапазонов из config.json

    Returns:
        bool: True если обновление успешно, иначе False
    """
    try:

        # Проверяем наличие секции price_rules в конфигурации
        if "price_rules" not in config:
            logger.error("В конфигурации отсутствует секция 'price_rules'")
            return False

        price_rules = config["price_rules"]

        logger.info(f"Найдено правил изменения цен: {len(price_rules)}")
        for rule in price_rules:
            logger.info(f"Диапазон {rule['min']}-{rule['max']}: +{rule['percentage']}%")

        logger.info(f"Открываем файл {output_xlsx}")
        df = pd.read_excel(output_xlsx)

        # Проверяем наличие колонки "Ціна"
        if "Ціна" not in df.columns:
            logger.error("Колонка 'Ціна' не найдена в файле")
            return False

        # Создаем копию исходного DataFrame
        updated_df = df.copy()

        # Счетчики для статистики
        total_rows = len(df)
        updated_rows = 0

        # Статистика по диапазонам
        range_stats = {f"{rule['min']}-{rule['max']}": 0 for rule in price_rules}

        # Проходим по всем строкам
        for index, row in df.iterrows():
            # Получаем текущую цену
            current_price_str = str(row["Ціна"]).strip()

            # Пропускаем пустые значения
            if not current_price_str or current_price_str.lower() == "nan":
                continue

            # Преобразуем строку с запятой в число с плавающей точкой
            try:
                current_price = float(current_price_str.replace(",", "."))
            except ValueError:
                logger.warning(
                    f"Невозможно преобразовать цену '{current_price_str}' в строке {index+1}"
                )
                continue

            # Ищем подходящее правило для цены
            applied_rule = None
            for rule in price_rules:
                min_price = float(rule["min"])
                max_price = float(rule["max"])

                if min_price <= current_price <= max_price:
                    applied_rule = rule
                    break

            # Если нашли подходящее правило, применяем его
            if applied_rule:
                percentage = float(applied_rule["percentage"])

                # Увеличиваем цену на указанный процент
                new_price = current_price * (1 + percentage / 100)

                # Форматируем цену обратно в строку с запятой
                new_price_str = str(round(new_price, 2)).replace(".", ",")

                # Обновляем цену в DataFrame
                updated_df.at[index, "Ціна"] = new_price_str

                # Обновляем статистику
                updated_rows += 1
                range_key = f"{applied_rule['min']}-{applied_rule['max']}"
                range_stats[range_key] += 1

                logger.debug(
                    f"Строка {index+1}: Цена изменена с {current_price_str} на {new_price_str} (+{percentage}%)"
                )

        # Сохраняем обновленный DataFrame в новый файл
        updated_df.to_excel(new_output_xlsx, index=False)

        # Выводим статистику по диапазонам
        logger.info("Статистика по диапазонам цен:")
        for range_key, count in range_stats.items():
            if count > 0:
                logger.info(f"  Диапазон {range_key}: изменено {count} позиций")

        logger.info(
            f"Обновление цен завершено. Обработано строк: {total_rows}, изменено: {updated_rows}"
        )
        logger.info(f"Результат сохранен в {new_output_xlsx}")

        return True

    except Exception as e:
        logger.error(f"Ошибка при обновлении цен: {str(e)}")
        return False


def main():

    # Загружаем конфигурацию

    logger.info("Запуск скрапера с параметрами из config.json:")
    logger.info(f"URL: {url}")
    logger.info(f"Начальная страница: {start_page}")
    logger.info(f"Количество страниц: {num_pages}")
    logger.info(f"Задержка: {delay} сек.")

    # Запрашиваем пользователя, какую операцию выполнить
    print("\nВыберите операцию:")
    print("1. Только скачать HTML-страницы")
    print("2. Только обработать существующие HTML-страницы")
    print("3. Работа с ценами на товар")
    print("4. Очистить временные файла")
    print("0. Выход")

    choice = input("Введите номер операции (1-3): ").strip()

    if choice == "1":
        # Только скачиваем страницы
        download_pages(url, start_page, num_pages, cookies, headers, delay)
        time.sleep(2)
    elif choice == "2":
        # Только обрабатываем существующие страницы
        process_html_files()
        time.sleep(2)
    elif choice == "3":

        update_prices_from_config()
        time.sleep(2)
    elif choice == "4":
        if os.path.exists(html_page):
            shutil.rmtree(html_page)
        html_page.mkdir(parents=True, exist_ok=True)
    elif choice == "0":
        logger.info("Выход из программы")
        exit(0)
    else:
        logger.error("Некорректный выбор операции")


if __name__ == "__main__":
    main()
