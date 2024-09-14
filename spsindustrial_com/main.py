from pathlib import Path
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import random
import gzip
import shutil
import csv
import random
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from configuration.logger_setup import logger
from bs4 import BeautifulSoup
import re
import base64
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET

import threading
import datetime
import json

# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
data_directory = current_directory / "data"
gz_directory = current_directory / "gz"
xml_directory = current_directory / "xml"
# html_directory = current_directory / "html"

data_directory.mkdir(parents=True, exist_ok=True)
gz_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
# html_directory.mkdir(parents=True, exist_ok=True)

xml_sitemap = data_directory / "sitemap_index.xml"
csv_url_site_maps = data_directory / "url_site_maps.csv"
csv_url_products = data_directory / "url_products.csv"
csv_file_successful = data_directory / "urls_successful.csv"
csv_result = data_directory / "result.csv"


cookies = {
    "LanguageId": "1033",
    "auth": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1laWQiOiJhbm9ueW1vdXMiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiI2Mzg2MjIwMTIzNTA2OTY3NDUiLCJsb2dpbnNlc3Npb25pZCI6ImFhM2ZmMDBiLTgzMzQtNDZmOC1hYmZjLWE1MjViZWI2NjEwZSIsInAiOiIxIiwibmJmIjoxNzI2MzQ1MjM1LCJleHAiOjE3MjY2MDQ0MzUsImlhdCI6MTcyNjM0NTIzNX0.zapAQ4niib1NsmBek8HjEyIGHcHN5Rk6G6SdtrrzMkQ",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    # 'cookie': 'LanguageId=1033; auth=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1laWQiOiJhbm9ueW1vdXMiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiI2Mzg2MjIwMTIzNTA2OTY3NDUiLCJsb2dpbnNlc3Npb25pZCI6ImFhM2ZmMDBiLTgzMzQtNDZmOC1hYmZjLWE1MjViZWI2NjEwZSIsInAiOiIxIiwibmJmIjoxNzI2MzQ1MjM1LCJleHAiOjE3MjY2MDQ0MzUsImlhdCI6MTcyNjM0NTIzNX0.zapAQ4niib1NsmBek8HjEyIGHcHN5Rk6G6SdtrrzMkQ',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


# Функция для скачивания XML по URL
def download_xml(url):
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    response = requests.get(
        url,
        cookies=cookies,
        headers=headers,
        proxies=proxies_dict,
    )
    response.raise_for_status()  # Если ошибка - выбросить исключение
    logger.info(response.status_code)
    return response.content


# Функция для парсинга основного sitemap и получения ссылок на другие sitemaps
def parse_main_sitemap(xml_content):
    sitemap_urls = []
    root = ET.fromstring(xml_content)
    for sitemap in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
        loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
        sitemap_urls.append(loc)
    logger.info(len(sitemap_urls))
    return sitemap_urls


# Функция для парсинга каждого подкарты и получения всех URL
def parse_sub_sitemap(xml_content):
    urls = []
    root = ET.fromstring(xml_content)
    for url in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
        loc = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
        urls.append(loc)
    return urls


# Основная функция для сбора всех URL из sitemaps
def collect_sitemap_urls():
    main_sitemap_url = "https://www.spsindustrial.com/sitemap.xml"
    # Скачиваем и разбираем основной sitemap
    main_sitemap_content = download_xml(main_sitemap_url)
    sitemap_urls = parse_main_sitemap(main_sitemap_content)

    all_urls = []

    # Скачиваем и разбираем каждую подкарту
    for sitemap_url in sitemap_urls:
        sitemap_content = download_xml(sitemap_url)
        urls = parse_sub_sitemap(sitemap_content)
        all_urls.extend(urls)

    # Записываем все ссылки в CSV файл
    df = pd.DataFrame(all_urls, columns=["url"])
    df.to_csv(csv_url_products, index=False)
    print(f"Ссылки успешно записаны в {csv_url_products}")


def get_successful_urls(csv_file_successful):
    """Читает успешные URL из CSV-файла и возвращает их в виде множества."""
    if not Path(csv_file_successful).exists():
        return set()

    with open(csv_file_successful, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        successful_urls = {row[0] for row in reader if row}
    return successful_urls


def get_html(max_workers):
    # Получение списка уже успешных URL
    successful_urls = get_successful_urls(csv_file_successful)
    proxies = load_proxies()  # Загружаем список всех прокси
    urls_df = pd.read_csv(csv_url_products)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                fetch_url,
                url,
                proxies,  # Передаем весь список прокси
                csv_file_successful,
                successful_urls,
            )
            for count, url in enumerate(urls_df["url"], start=1)
        ]

        for future in as_completed(futures):
            try:
                result = future.result()  # Получаем результат выполнения задачи
                if result == 403:
                    return (
                        403  # Возвращаем ошибку 403 для обработки в основной программе
                    )
            except Exception as e:
                logger.error(f"Error occurred: {e}")


def fetch_url(url, proxies, csv_file_successful, successful_urls):
    fetch_lock = threading.Lock()  # Локальная

    if url in successful_urls:
        logger.info(f"| Объявление уже было обработано, пропускаем. |")
        return
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}
    try:
        response = requests.get(
            url,
            headers=headers,
            cookies=cookies,
            proxies=proxies_dict,
            timeout=60,  # Тайм-аут для предотвращения зависания
        )
        logger.info(url)
        # response.raise_for_status()
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            success = parsing(soup, url, csv_file_successful)
            if success:
                with fetch_lock:
                    successful_urls.add(url)
                    write_to_csv(url, csv_file_successful)
            return

        elif response.status_code == 403:
            logger.error("Ошибка 403: доступ запрещен. Возвращаемся к выбору действий.")
            return 403  # Возвращаем специальный код ошибки 403
        else:
            logger.error(f"Ошибка {response.status_code}")

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")


def parsing(soup, url, csv_file_successful):
    parsing_lock = threading.Lock()  # Локальная блокировка

    try:
        page_title = None
        price = None
        description = None
        sku_item_n = None
        brand = None
        part = None
        upc = None
        min_order_qty = None
        page_title = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(1) > h1"
        )
        if page_title:
            page_title = page_title.text
        else:
            page_title = None

        description = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(3) > div > div > div > div > div:nth-child(1) > div"
        )
        if description:
            description = description.text.replace("Description", "")
        else:
            description = None

        price = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(10) > div > span"
        )
        if price:
            price = price.text
        else:
            price = None

        sku_item_n = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(2) > div"
        )
        if sku_item_n:
            sku_item_n = sku_item_n.text.replace("Item No.", "")
        else:
            sku_item_n = None

        upc_element = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(4) > div > span:nth-child(2)"
        )

        if upc_element:
            upc = upc_element.text
        else:
            upc = None  # Или любое другое значение по умолчанию

        brand = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(3) > div > span:nth-child(2)"
        )
        if brand:
            brand = brand.text
        else:
            brand = None

        manufacturer_name = brand
        part = upc
        data = data = (
            f"{url};{page_title};{description};{price};{min_order_qty};{sku_item_n};{upc};{brand};{manufacturer_name};{part}"
        )
        logger.info(data)
        write_to_csv(data, csv_result)
        return True
    except Exception as ex:
        logger.error(ex)


def write_to_csv(data, filename):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{data}\n")


def remove_successful_urls():
    # Проверяем, если файл с успешными URL пустой
    if csv_file_successful.stat().st_size == 0:
        logger.info("Файл urls_successful.csv пуст, ничего не делаем.")
        return

    # Загружаем данные из обоих CSV файлов
    try:
        # Читаем csv_url_products с заголовком
        df_products = pd.read_csv(csv_url_products)

        # Читаем csv_file_successful без заголовка и присваиваем имя столбцу
        df_successful = pd.read_csv(csv_file_successful, header=None, names=["url"])
    except FileNotFoundError as e:
        logger.error(f"Ошибка: {e}")
        return

    # Проверка на наличие столбца 'url' в df_products
    if "url" not in df_products.columns:
        logger.info("Файл url_products.csv не содержит колонку 'url'.")
        return

    # Удаляем успешные URL из списка продуктов
    initial_count = len(df_products)
    df_products = df_products[~df_products["url"].isin(df_successful["url"])]
    final_count = len(df_products)

    # Если были удалены какие-то записи
    if initial_count != final_count:
        # Перезаписываем файл csv_url_products
        df_products.to_csv(csv_url_products, index=False)
        logger.info(
            f"Удалено {initial_count - final_count} записей из {csv_url_products.name}."
        )

        # Очищаем файл csv_file_successful
        open(csv_file_successful, "w").close()
        logger.info(f"Файл {csv_file_successful.name} очищен.")
    else:
        print("Не было найдено совпадающих URL для удаления.")


if __name__ == "__main__":
    # Пример использования

    # collect_sitemap_urls()
    remove_successful_urls()
    max_workers = 50
    result = get_html(max_workers)
