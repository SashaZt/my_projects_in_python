from concurrent.futures import ThreadPoolExecutor, as_completed
from phonenumbers import NumberParseException
from configuration.logger_setup import logger
from selectolax.parser import HTMLParser
from mysql.connector import errorcode
import xml.etree.ElementTree as ET
from pathlib import Path
import mysql.connector
import phonenumbers
import pandas as pd
import threading
import datetime
import requests
import random
import locale
import csv
import re

# Параметры подключения к базе данных
config = {
    "user": "python_mysql",
    "password": "python_mysql",
    "host": "localhost",
    "database": "parsing",
}

belarus_phone_patterns = {
    "full": r"\b(80\d{9}|375\d{9}|\d{9})\b",
    "split": r"(375\d{9})",
    "final": r"\b(\d{9})\b",
    "codes": [375],
}
cookies = {
    "cf_clearance": "monQDzP_waHOvZh0.hDAsR94im9uE96lwcdnX2hrdEY-1725446097-1.2.1.1-chJt2ZkEh9UrKx1A7jox4JZI8dzz4oRcv8f08iESnPGJk9U3Yk9w4lZPjIROmziDGEnthqSriV3TqB9wPp6lVDhsZtv5Q74mx3KMyU91TKvAKy1dIwcF0z678m25M57WH5M18tEAff_6lg2RI7KlDybiE2DGFrH9TJXAcJornUJJFVqbb_79cB.gzRdKp2t.pguXWE_hz68LRJMXangOAs.hgov_QYvSJCJDtv_hK8QxESu0vBukzQolHZ453C7zrC7kvI2q3zhe3657X4TJuEswD2s07r0FENU3FnT9JqF47szoF7kwXCQ3dHgfI4Kc053rg3.JmPh29_ruEKH3MpIpcXRc_STiib8rnUfaeONt87wwXHM3oDTO6r4z7gK5ax0zutIIpLIGAXnY2nC3eUlwYTqCNV5Dau6Cb2O3Um0AwvzUqoq_8Gg2i2r7NcTD",
}


headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "cache-control": "no-cache",
    # 'cookie': 'PODID=app0; currency=EUR; language=en; beforeUnloadTime=1725012465978; unloadTime=1725012466123; cf_clearance=uO_9Q0ltGzdCJtfg8IHmM2Cb.8ifsy18fZQO5vEO7ow-1725444391-1.2.1.1-t.5fXdX_4bS4ETu4zErizDgE7Vy7plKpW1WHdDUCpdBb1AEdUFiufnr1G3PvUgV9QqqWK8P9RC15T7P_oDdgIN46kl.Avs8oAlxRANMFnljckwlFBgdza25DOnirIiKcl7tPP4mPngXMV0H.Tifa179fVhu7VKhmMCnuR.NdiayABXJpt33sF3vZrQgfgFNfZWLVHQSkdefGyyce2hejOFBD7.dHsdwJRXtGp_mbu79YhXZYyRxzV3mEFvFdOxIiQZuLAKVynW5odxvuhPddJ7gFPINEIU72OPilaESa4vDp..gbaV3_nrYjai.qo5cRzTAP0FuiEPTsW79TYsSfip.p9Av3BWkO6.QfKrGT57PpOSYN8hWj066_Jls9Oz3a2on_G3hAu8CI4N.f5yIPEzo2GPYMPiE8CmaWkdxD_pzX5k9KGOr6UUrcxBJBMCyY; SESSION=b10e54a3-f08b-4b0c-b939-26a8bef4fda6.app-0',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"128.0.6613.114"',
    "sec-ch-ua-full-version-list": '"Chromium";v="128.0.6613.114", "Not;A=Brand";v="24.0.0.0", "Google Chrome";v="128.0.6613.114"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"15.0.0"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}
# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)

"""Читает и форматирует прокси-серверы из файла."""


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


# Список начальных URL с картами сайтов
SITEMAP_URLS = [
    "https://aleo.com/sitemap_company_profile_int.xml",
    "https://aleo.com/sitemap_company_profile_pl.xml",
]


# Функция для загрузки XML файла
def download_xml(url):
    proxies = load_proxies()
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}
    try:
        response = requests.get(
            url,
            # proxies=proxies_dict,
            headers=headers,
            cookies=cookies,
        )
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.error(f"Ошибка при загрузке {url}: {e}")
        return None


# Функция для парсинга XML файла в объект ElementTree
def parse_xml(content):
    try:
        return ET.fromstring(content)
    except ET.ParseError as e:
        logger.error(f"Ошибка парсинга XML: {e}")
        return None


# Функция для получения всех <loc> ссылок из sitemap файла
def get_sitemap_links(root):
    namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = []
    for sitemap in root.findall("ns:sitemap", namespaces):
        loc = sitemap.find("ns:loc", namespaces).text
        locs.append(loc)
    return locs


# Функция для получения всех <loc> ссылок на компании
def get_company_links(root):
    namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    company_links = []
    for url in root.findall("ns:url", namespaces):
        loc = url.find("ns:loc", namespaces).text
        company_links.append(loc)
    return company_links


# Функция для обработки sitemap: скачиваем и извлекаем ссылки на другие XML
def process_sitemap(url):
    content = download_xml(url)
    if content:
        root = parse_xml(content)
        if root:
            return get_sitemap_links(root)
    return []


# Функция для обработки дополнительных файлов с компаниями
def process_company_sitemap(url):
    content = download_xml(url)
    if content:
        root = parse_xml(content)
        if root:
            return get_company_links(root)
    return []


# Функция для сохранения всех ссылок в CSV файл
def save_to_csv(filename, links):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["url"])  # Заголовок
        for link in links:
            writer.writerow([link])
    logger.info(f"Сохранено {len(links)} ссылок в файл {filename}")


# Основная функция для выполнения всех шагов
def main():
    all_company_links = []

    # Шаг 1: Обрабатываем начальные sitemap файлы
    for sitemap_url in SITEMAP_URLS:
        sitemap_links = process_sitemap(sitemap_url)

        # Шаг 2: Обрабатываем каждый полученный sitemap для компаний
        for link in sitemap_links:
            company_links = process_company_sitemap(link)
            all_company_links.extend(company_links)

    # Шаг 3: Сохраняем результаты в CSV файл
    save_to_csv("company_links.csv", all_company_links)


# Запуск основного процесса
if __name__ == "__main__":
    main()
