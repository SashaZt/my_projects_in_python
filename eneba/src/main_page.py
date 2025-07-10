# src/main_page.py

import asyncio
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
from downloader import downloader
from loguru import logger
from main_bd import load_and_save_data, update_unique_ids_in_db
from path_manager import get_path, is_initialized, select_category_and_init_paths
from rozetka_manager import rozetka_manager
from rozetka_path_manager import get_rozetka_path

BASE_URL = "https://www.eneba.com/"
# Базовая директория — текущая рабочая директория
BASE_DIR = Path(__file__).parent.parent
config = load_config()

cookies = config["cookies"]
headers = config["headers"]
# Получаем инициализированные пути


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
        # logger.info(f"Загрузка страницы: {url}")
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

        # # Получаем цену в UAH и делим на 100
        # price_uah = None
        # price_data_eur = auction.get('price({"currency":"EUR"})')
        # price_data_uah = auction.get('price({"currency":"UAH"})')

        # if price_data and "amount" in price_data:
        #     price_uah_str = str(price_data["amount"] / 100)
        #     if price_uah_str:
        #         price_uah_float = float(price_uah_str)
        #         price_uah_rounded = math.ceil(price_uah_float)
        #         price_uah = str(price_uah_rounded).replace(
        #             ".", ","
        #         )  # Преобразуем обратно в строку и меняем точку на запятую
        #     else:
        #         price_uah = None

        # Получаем имя продукта
        product_name = product.get("name", "")

        if product_name:
            # Удаляем "XBOX LIVE Key" из названия
            product_name = (
                product_name.replace("XBOX LIVE Key", "")
                .replace("Xbox Live Key", "")
                .replace("(Xbox One)", "")
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
        cleaned_name = clean_product_name(product_name)

        price_uah = None
        currency_eur = config["currency_eur"]
        # Получаем данные о ценах
        price_data_eur = auction.get('price({"currency":"EUR"})')
        price_data_uah = auction.get('price({"currency":"UAH"})')
        # Логирование для отладки

        if price_data_eur and "amount" in price_data_eur:
            # Конвертируем EUR в UAH
            price_amount = price_data_eur["amount"] / 100  # Из копеек в EUR
            price_uah_float = price_amount * currency_eur  # Конвертируем в UAH
            price_uah_rounded = math.ceil(price_uah_float)  # Округляем вверх
            price_uah = str(price_uah_rounded).replace(".", ",")

        elif price_data_uah and "amount" in price_data_uah:
            # Используем UAH напрямую
            price_amount = price_data_uah["amount"] / 100  # Из копеек в UAH
            price_uah_rounded = math.ceil(price_amount)  # Округляем вверх
            price_uah = str(price_uah_rounded).replace(".", ",")
        price_uah = int(price_uah)

        # Проверяем цену перед преобразованием в float
        if price_uah is None:
            continue

        # Пропускаем товары дороже 1000 UAH
        if price_uah_float > 1000:
            logger.debug(f"Товар {product_slug_str} дорогой {price_uah}")
            continue

        product_data = {
            "product_slug": product_slug_str,
            "product_name": product_name,
            "price": price_uah,
            "image_url": img_url,
            "cleaned_name": cleaned_name,
        }

        # Используем менеджер категорий для форматирования шаблона
        item = category_manager.format_item_template(product_data)
        # Проверка, что поле cleaned_name не попадет в итоговый результат
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


def download_pages(base_url, cookies, headers):
    """
    Скачивает HTML-страницы с сайта и сохраняет их в директорию html

    Args:
        base_url (str): Базовый URL с фильтрами
        cookies (dict): Куки для запроса
        headers (dict): Заголовки для запроса

    Returns:
        int: Количество успешно скачанных страниц
    """
    # Проверяем существующие файлы HTML
    start_page = get_path("start_page")
    num_pages = get_path("num_pages")
    delay = get_path("delay")
    html_page = get_path("html_page")

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

    # ИСПРАВЛЕНО: Подготавливаем ВСЕ URL и файлы сразу
    urls = []
    custom_filenames = {}

    for page in pages_to_download:
        # Создаем URL для страницы
        page_url = build_url_for_page(base_url, page)

        # Создаем имя файла для страницы
        page_html_file = html_page / f"eneba_page_{page}.html"

        # Добавляем в списки
        urls.append(page_url)
        custom_filenames[page_url] = page_html_file

    async def download_all_pages():
        results = await downloader.download_urls(urls, custom_filenames)
        return results

    # Запускаем многопоточную загрузку
    logger.info(f"🚀 Запуск многопоточной загрузки {len(urls)} страниц")
    results = asyncio.run(download_all_pages())

    # Подсчитываем результаты
    successful_downloads = sum(1 for success in results.values() if success)
    failed_downloads = len(results) - successful_downloads

    logger.info(f"✅ Успешно скачано страниц: {successful_downloads}")
    if failed_downloads > 0:
        logger.warning(f"❌ Ошибок при скачивании: {failed_downloads}")

    # Возвращаем общее количество страниц (существующие + новые)
    return len(existing_files) + successful_downloads


def process_html_files():
    """
    Обрабатывает HTML-файлы в директории html и создает Excel-файл с товарами

    Returns:
        list: Список всех товаров
    """
    html_page = get_path("html_page")
    output_json = get_path("output_json")
    output_xlsx = get_path("output_xlsx")

    logger.info("Начинаем обработку HTML-файлов...")

    all_products = []
    files = list(html_page.glob("*.html"))
    all_urls = []
    for html_file in files:

        # Извлекаем данные Apollo State
        apollo_data = scrap_html(html_file)
        if apollo_data:
            # Обрабатываем данные Apollo State
            page_products, urls = process_apollo_data(apollo_data)

            # Добавляем продукты к общему списку
            all_products.extend(page_products)
            all_urls.extend(urls)
            # logger.info(f"Извлечено товаров из {html_file.name}: {len(page_products)}")
        else:
            logger.error(
                f"Не удалось извлечь данные Apollo State из файла {html_file.name}"
            )
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
    output_xlsx = get_path("output_xlsx")
    new_output_xlsx = get_path("new_output_xlsx")

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
        # ИСПРАВЛЕНО: Явно конвертируем колонку "Ціна" в строковый тип
        df["Ціна"] = df["Ціна"].astype(str)
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
                price_uah_rounded = math.ceil(new_price)
                # Форматируем цену обратно в строку с запятой
                new_price_str = str(round(price_uah_rounded, 2)).replace(".", ",")

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


def update_prices_from_config_rozetka():
    """
    Обновляет цены в Excel файле на основе ценовых диапазонов из config.json

    Returns:
        bool: True если обновление успешно, иначе False
    """
    output_xlsx = get_rozetka_path("output_xlsx")
    new_output_xlsx = get_rozetka_path("new_output_xlsx")

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
        # ИСПРАВЛЕНО: Явно конвертируем колонку "Ціна" в строковый тип
        df["Ціна"] = df["Ціна"].astype(str)
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
                price_uah_rounded = math.ceil(new_price)
                # Форматируем цену обратно в строку с запятой
                new_price_str = str(round(price_uah_rounded, 2)).replace(".", ",")

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


def extract_ids_from_excel():
    """
    Извлекает Код_товару и Унікальний_ідентифікатор из Excel-файла

    Args:
        file_path (str): Путь к Excel-файлу

    Returns:
        dict: Словарь с product_code в качестве ключа и unique_id в качестве значения
    """
    export_xlsx = get_path("export_xlsx")

    try:
        export_xlsx = f"{BASE_DIR}/data/export-products.xlsx"
        # Загружаем Excel-файл
        logger.info(f"Загрузка Excel-файла: {export_xlsx}")
        df = pd.read_excel(export_xlsx)

        # Получаем реальные названия колонок
        column_names = list(df.columns)
        # logger.info(f"Найденные колонки в файле: {column_names}")

        # Словарь для маппинга возможных имен колонок
        column_mapping = {
            "Назва_позиції": ["Назва_позиції"],
            "Унікальний_ідентифікатор": ["Унікальний_ідентифікатор"],
        }

        # Находим реальные имена колонок
        real_columns = {}
        for req_col, possible_names in column_mapping.items():
            found = False
            for name in possible_names:
                if name in column_names:
                    real_columns[req_col] = name
                    found = True
                    break

            if not found:
                # Если колонка не найдена по имени, попробуем по индексу
                if req_col == "Назва_позиції" and len(column_names) > 0:
                    # Первая колонка (A)
                    real_columns[req_col] = column_names[0]
                    logger.warning(
                        f"Колонка 'Назва_позиції' не найдена по имени. Используем первую колонку: {column_names[0]}"
                    )
                elif req_col == "Унікальний_ідентифікатор" and len(column_names) > 24:
                    # 25-я колонка (Y)
                    real_columns[req_col] = column_names[24]
                    logger.warning(
                        f"Колонка 'Унікальний_ідентифікатор' не найдена по имени. Используем колонку Y: {column_names[24]}"
                    )
                else:
                    logger.error(f"Не удалось найти колонку {req_col} в файле")
                    return None

        logger.info(f"Используемые колонки: {real_columns}")

        # Извлекаем данные
        result = {}
        for idx, row in df.iterrows():
            product_code = row[real_columns["Назва_позиції"]]
            unique_id = row[real_columns["Унікальний_ідентифікатор"]]

            # Пропускаем записи с пустыми значениями
            if pd.isna(product_code) or pd.isna(unique_id):
                continue

            # Преобразуем значения к строкам
            product_code = str(product_code).strip()
            unique_id = str(unique_id).strip()

            # Добавляем в результат, только если оба значения не пусты
            if product_code and unique_id:
                # Используем нижний регистр для ключа словаря
                result[product_code] = unique_id

        logger.info(f"Извлечено {len(result)} пар ID из Excel-файла")
        update_unique_ids_in_db(result)
        return result

    except Exception as e:
        logger.error(f"Ошибка при обработке Excel-файла: {str(e)}")
        return None


def main():
    categories = category_manager.get_categories()
    print("\nДоступные категории:")
    for i, (cat_id, cat_info) in enumerate(categories.items(), 1):
        print(f"{i}. {cat_info['name']} (ID: {cat_id})")

    try:
        cat_choice = int(input("\nВыберите категорию (номер): "))
        cat_keys = list(categories.keys())
        selected_category = cat_keys[cat_choice - 1]

        # # Инициализируем пути для выбранной категории
        # if not init_category_paths(selected_category):
        #     logger.error("Не удалось инициализировать пути для категории")
        #     return

        logger.info(f"Выбрана категория: {categories[selected_category]['name']}")
    except (ValueError, IndexError):
        logger.error("Некорректный выбор категории")
        return

    # Загружаем конфигурацию
    url = get_path("url")
    start_page = get_path("start_page")
    num_pages = get_path("num_pages")
    delay = get_path("delay")
    html_page = get_path("html_page")

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
        time.sleep(2)
        # Только скачиваем страницы
        download_pages(url, start_page, num_pages, cookies, headers, delay)

    elif choice == "2":
        time.sleep(2)
        # Только обрабатываем существующие страницы
        process_html_files()
    elif choice == "3":
        time.sleep(2)

        update_prices_from_config()

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
