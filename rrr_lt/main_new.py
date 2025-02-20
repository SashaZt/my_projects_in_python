import json
import re
import sys
import time
import urllib.parse
from collections import OrderedDict
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger

# API_KEY = "6c54502fd688c7ce737f1c650444884a"
API_KEY = "b7141d2b54426945a9f0bf6ab4c7bc54"
# Настройте максимальное количество попыток, если требуется
MAX_RETRIES = 10
RETRY_DELAY = 30  # Задержка между попытками в секундах


current_directory = Path.cwd()
html_code_directory = current_directory / "html_code"
json_product_directory = current_directory / "json_product"
log_directory = current_directory / "log"
data_directory = current_directory / "data"
log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
json_product_directory.mkdir(parents=True, exist_ok=True)
html_code_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
xlsx_result = data_directory / "result.xlsx"
output_csv_file = data_directory / "output.csv"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def main_config():
    # Парсим данные из файла
    headers, cookies = parse_curl_from_file("config.txt")

    # Фильтруем только нужные ключи
    filtered_headers, filtered_cookies = filter_required_data(headers, cookies)

    return filtered_headers, filtered_cookies


def parse_curl_from_file(file_path="config.txt"):
    # Читаем файл config.txt
    with open(file_path, "r", encoding="utf-8") as f:
        curl_data = f.read().strip()

    # Инициализируем словари для headers и cookies
    headers = {}
    cookies = {}

    # Извлекаем заголовки (-H)
    header_matches = re.findall(r"-H\s+'([^']+)'", curl_data)
    for header in header_matches:
        key, value = header.split(": ", 1)  # Разделяем ключ и значение
        headers[key.lower()] = value  # Приводим ключ к нижнему регистру

    # Извлекаем куки (-b)
    cookie_match = re.search(r"-b\s+'([^']+)'", curl_data)
    if cookie_match:
        cookie_string = cookie_match.group(1)
        # Парсим строку кук в словарь
        cookie_pairs = cookie_string.split("; ")
        for pair in cookie_pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)
                cookies[key] = value

    return headers, cookies


def filter_required_data(headers, cookies):
    # Определяем нужные ключи для headers
    required_headers_keys = {
        "accept",
        "accept-language",
        "x-requested-with",
    }

    # Определяем нужные ключи для cookies
    required_cookies_keys = {
        "ci_session",
        "ff_ux_sid",
        "cart_session",
        "CookieConsent",
        "soundestID",
        "omnisendSessionID",
        "disable_ovoko_modal",
        "wishlist",
    }

    # Фильтруем headers
    filtered_headers = {
        key: headers[key] for key in required_headers_keys if key in headers
    }

    # Фильтруем cookies
    filtered_cookies = {
        key: cookies[key] for key in required_cookies_keys if key in cookies
    }

    return filtered_headers, filtered_cookies


def submit_batch_jobs(product_ids):
    """
    Отправляет batch-запрос в ScraperAPI для нескольких продуктов.
    """
    headers, cookies = main_config()
    cookie_string = "; ".join(f"{key}={value}" for key, value in cookies.items())
    headers["Cookie"] = cookie_string

    # Формируем список URL для каждого продукта
    urls = []
    for id_product in product_ids:
        json_file = json_product_directory / f"{id_product}.json"
        if json_file.exists():
            logger.info(f"Файл {json_file} уже существует. Пропускаем {id_product}.")
            continue

        base_url = "https://rrr.lt/ru/poisk"
        query_params = {"q": id_product, "prs": "2", "page": "1"}
        full_url = f"{base_url}?{urllib.parse.urlencode(query_params)}"
        urls.append(full_url)

    if not urls:
        logger.info("Все файлы уже существуют. Нечего скачивать.")
        return []

    # Параметры для batch-запроса
    payload = {
        "apiKey": API_KEY,
        "urls": urls,  # Список URL
        "apiParams": {
            "keep_headers": "true",  # Сохранение пользовательских заголовков
        },
    }
    logger.info(payload)
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(
                "https://async.scraperapi.com/batchjobs",
                json=payload,
                headers=headers,
                timeout=60,
            )
            if response.status_code == 200:
                return response.json()  # Возвращаем список задач
            else:
                logger.warning(
                    f"Ошибка {response.status_code} при отправке batch-запроса. Попытка {retries + 1}/{MAX_RETRIES}."
                )
        except Exception as e:
            logger.error(
                f"Ошибка при отправке batch-запроса: {e}. Попытка {retries + 1}/{MAX_RETRIES}."
            )
        retries += 1
        time.sleep(RETRY_DELAY)

    logger.error("Не удалось отправить batch-запрос после всех попыток.")
    raise Exception("Не удалось отправить batch-запрос к ScraperAPI.")


def check_batch_status(status_urls):
    """
    Проверяет статус всех задач и сохраняет результаты, когда они готовы.
    """
    results = {}
    for status_url in status_urls:
        retries = 0
        while retries < MAX_RETRIES:
            try:
                response = requests.get(status_url, timeout=60)
                if response.status_code != 200:
                    logger.warning(
                        f"Ошибка {response.status_code} при проверке {status_url}."
                    )
                    retries += 1
                    time.sleep(RETRY_DELAY)
                    continue

                job_data = response.json()
                job_id = job_data["id"]
                status = job_data["status"]
                original_url = job_data["url"]

                # Извлекаем id_product из URL
                id_product = urllib.parse.parse_qs(
                    urllib.parse.urlparse(original_url).query
                )["q"][0]
                json_file = json_product_directory / f"{id_product}.json"

                if status == "finished":
                    # Сохраняем результат
                    with open(json_file, "w", encoding="utf-8") as file:
                        json.dump(
                            job_data["response"], file, ensure_ascii=False, indent=4
                        )
                    logger.info(f"Скачано и сохранено: {json_file}")
                    results[id_product] = job_data["response"]
                    break
                elif status == "running":
                    logger.info(f"Задача для {id_product} еще выполняется. Ждем...")
                else:
                    logger.error(f"Неизвестный статус {status} для {id_product}.")
                    break

            except Exception as e:
                logger.error(f"Ошибка при проверке статуса {status_url}: {e}")

            retries += 1
            time.sleep(RETRY_DELAY)

        if retries >= MAX_RETRIES:
            logger.error(
                f"Не удалось получить результат для {status_url} после {MAX_RETRIES} попыток."
            )
            results[id_product] = None

    return results


def get_pages_html_batch(product_ids):
    """
    Основная функция для batch-загрузки страниц.
    """
    # Отправляем batch-запрос
    batch_response = submit_batch_jobs(product_ids)
    if not batch_response:
        return {}

    # Извлекаем statusUrl для каждой задачи
    status_urls = [job["statusUrl"] for job in batch_response]

    # Проверяем статус и сохраняем результаты
    results = check_batch_status(status_urls)
    return results


# Пример использования
if __name__ == "__main__":
    # Список продуктов для загрузки
    product_ids = ["5802243444", "735513182", "7422R9"]
    json_product_directory.mkdir(
        parents=True, exist_ok=True
    )  # Создаем папку, если её нет

    results = get_pages_html_batch(product_ids)
    for product_id, result in results.items():
        if result:
            logger.info(f"Успешно загружен {product_id}")
        else:
            logger.error(f"Ошибка загрузки {product_id}")
