# МНОГОПОТОЧНОСТЬ И ОЧЕРЕДЬ
import json
import os
import random
import time
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
file_proxy = configuration_directory / "roman.txt"


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


# Функция загрузки списка прокси
def load_proxies():
    if os.path.exists(file_proxy):
        with open(file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        logger.info(f"Загружено {len(proxies)} прокси.")
        return proxies
    else:
        logger.warning(
            "Файл с прокси не найден. Работа будет выполнена локально без прокси."
        )
        return []


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


# Основная функция для работы с ID
def get_html(url):
    cookies = {
        "consentUUID": "6cb56b4f-3f34-435d-b1d3-c1977cb47e33_38",
        "euconsent-v2": "CQJXf4AQJXf4AAjABCENBSFgAP_AAEPAACgAIzBV5CpMDWFAMHBRYNMgGYAW10ARIEQAABCBAyABCAOA8IAA0QECMAQAAAACAAIAoBABAAAAAABEAEAAIAAAAABEAAAAAAAIIAAAAAEQQAAAAAgAAAAAEAAIAAABAAQAkAAAAYKABEAAAIAgCAAAAAABAAAAAAMACAAIAAAAAAIAgAAAAAIAAAAAAEEAARAyyAYAAgABQAFwAtgD7AJSAa8A_oC6AGCAMhAZYAMEgQgAIAAWABUADgAIIAZABoAEQAJgAVQA3gB-AEJAIYAiQBLACaAGGAMoAc8A-wD9AIoARoAkQBcwDFAG0ANwAcQBQ4C8wGrgOCAeOBCEdAkAAWABUADgAIIAZABoAEQAJgAVQAuABiADeAH6AQwBEgCWAE0AMMAZQA0QBzwD7AP2AigCLAEiALmAYoA2gBuADiAIvATIAocBeYDLAGmgNXAeOA_shANAAWAFUALgAYgA3gDnAIoASkAuYBigDaAPHAf2SgHgAIAAWABwAIgATAAqgBcADFAIYAiQB-AFzAMUAi8BeYEISkB4ABYAFQAOAAggBkAGgARAAmABSACqAGIAP0AhgCJAGUANEAc8A_AD9AIsASIAuYBigDaAG4AReAocBeYDLAHBAPHAf2BCEqACAAUAFsAA.YAAAAAAAAAAA",
        "consentDate": "2024-12-09T10:15:57.293Z",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://www.focus-gesundheit.de/suche/allgemein-hausaerzte/deutschland",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    path = urlparse(url).path
    last_part = path.split("/")[-1].replace("-", "_")

    file_name = html_directory / f"{last_part}.html"
    if file_name.exists():
        return
    proxy = {
        "http": "http://5.79.73.131:13010",
        "https": "http://5.79.73.131:13010",
    }
    try:
        response = requests.get(
            url=url,
            # proxies=proxy,
            cookies=cookies,
            headers=headers,
            timeout=30,
        )
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
        logger.error(f"Неизвестная ошибка для  {url}")


# # Основной запуск с очередями и ThreadPoolExecutor
# if __name__ == "__main__":
#     all_urls = read_cities_from_csv(output_csv)
#     max_workers = 50  # Количество одновременно работающих потоков
#     # Загрузка прокси
#     proxies = load_proxies()
#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         future_to_id = {executor.submit(get_html, url): url for url in all_urls}

#         for future in as_completed(future_to_id):
#             url = future_to_id[future]
#             try:
#                 future.result()  # Проверяем исключения в выполнении задач
#             except Exception as e:
#                 logger.error(f"Ошибка при обработке ID {url}: {e}")

#     logger.info("Все задачи завершены.")
if __name__ == "__main__":
    max_workers = 50  # Количество одновременно работающих потоков
    proxies = load_proxies()  # Загрузка прокси

    while True:
        all_urls = read_cities_from_csv(output_csv)  # Заново считываем URL-ы
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
