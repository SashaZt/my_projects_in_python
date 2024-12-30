# МНОГОПОТОЧНОСТЬ И ОЧЕРЕДЬ
import json
import os
import random
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from configuration.logger_setup import logger

# Путь к папкам
current_directory = Path.cwd()
html_directory = current_directory / "html"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"
html_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
output_csv = data_directory / "output.csv"
file_proxy = configuration_directory / "1000ip.txt"


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


# Функция для парсинга прокси
def parse_proxy(proxy):
    """
    Парсит прокси в формате 'http://user:pass@host:port'
    """
    if "@" in proxy:
        protocol, rest = proxy.split("://", 1)
        credentials, server = rest.split("@", 1)
        username, password = credentials.split(":", 1)
        return {
            "server": f"{protocol}://{server}",
            "username": username,
            "password": password,
        }
    else:
        return {"server": f"http://{proxy}"}


# Функция для безопасного создания имени файла
def safe_filename_from_url(url: str) -> str:
    # Парсим путь из URL
    path = urllib.parse.urlparse(url).path
    # Получаем последние элементы из пути и заменяем "-" на "_"
    parts = path.strip("/").split("/")
    sanitized_parts = [
        re.sub(r"[^a-zA-Z0-9_]", "_", part.replace("-", "_")) for part in parts
    ]
    # Объединяем безопасные части пути
    filename = "_".join(sanitized_parts)
    return filename


# Основная функция для работы с ID
def get_html(url):

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    path = safe_filename_from_url(url)

    file_name = html_directory / f"{path}.html"
    if file_name.exists():
        return
    try:
        response = requests.get(
            url=url,
            # proxies=proxies_dict,
            headers=headers,
            timeout=30,
        )
        # Принудительно указываем кодировку UTF-8
        response.encoding = "utf-8"

        if response.status_code == 200:
            src = response.text
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(src)

        else:
            logger.warning(f"Ошибка ответа: {response.status_code} для  {url}")
    except requests.exceptions.ReadTimeout:
        logger.error(f"Тайм-аут при обработке  {url}")
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL ошибка для  {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса для  {url}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка для  {url} {e}")


#     logger.info("Все задачи завершены.")
if __name__ == "__main__":
    max_workers = 50  # Количество одновременно работающих потоков
    # proxies = load_proxies()  # Загрузка прокси
    while True:
        all_urls = read_cities_from_csv(output_csv)  # Заново считываем URL-ы
        # proxies = load_proxies()  # Загружаем список всех прокси
        if not all_urls:
            logger.info("Список URL пуст. Ожидание новых данных...")
            time.sleep(1)  # Ждем перед новой проверкой
            continue

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(get_html, url): url for url in all_urls}

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    future.result()  # Проверяем исключения в выполнении задач
                except Exception as e:
                    logger.error(f"Ошибка при обработке URL {url}: {e}")
