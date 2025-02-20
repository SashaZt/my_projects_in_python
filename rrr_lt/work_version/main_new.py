import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from loguru import logger

# Настройка глобальных переменных
API_KEY = "b7141d2b54426945a9f0bf6ab4c7bc54"
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
batch_file = json_product_directory / "batch_request.json"

logger.remove()
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def main_config():
    headers, cookies = parse_curl_from_file("config.txt")
    filtered_headers, filtered_cookies = filter_required_data(headers, cookies)
    return filtered_headers, filtered_cookies


def parse_curl_from_file(file_path="config.txt"):
    with open(file_path, "r", encoding="utf-8") as f:
        curl_data = f.read().strip()
    headers = {}
    cookies = {}
    header_matches = re.findall(r"-H\s+'([^']+)'", curl_data)
    for header in header_matches:
        key, value = header.split(": ", 1)
        headers[key.lower()] = value
    cookie_match = re.search(r"-b\s+'([^']+)'", curl_data)
    if cookie_match:
        cookie_string = cookie_match.group(1)
        cookie_pairs = cookie_string.split("; ")
        for pair in cookie_pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)
                cookies[key] = value
    return headers, cookies


def filter_required_data(headers, cookies):
    required_headers_keys = {"accept", "accept-language", "x-requested-with"}
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
    filtered_headers = {
        key: headers[key] for key in required_headers_keys if key in headers
    }
    filtered_cookies = {
        key: cookies[key] for key in required_cookies_keys if key in cookies
    }
    return filtered_headers, filtered_cookies


def submit_batch_jobs(product_ids):
    """
    Отправляет batch-запрос в ScraperAPI и сохраняет ответ в файл.
    """
    headers, cookies = main_config()
    cookie_string = "; ".join(f"{key}={value}" for key, value in cookies.items())
    headers["Cookie"] = cookie_string

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
        return None

    payload = {"apiKey": API_KEY, "urls": urls, "apiParams": {"keep_headers": "true"}}

    if batch_file.exists():
        logger.info(f"Файл batch-запроса {batch_file} уже существует. Используем его.")
        with open(batch_file, "r", encoding="utf-8") as f:
            return json.load(f)
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
                batch_data = response.json()
                with open(batch_file, "w", encoding="utf-8") as f:
                    json.dump(batch_data, f, ensure_ascii=False, indent=4)
                logger.info(f"Batch-запрос сохранен в {batch_file}")
                return batch_data
            else:
                logger.warning(
                    f"Ошибка {response.status_code} при отправке batch-запроса: {response.text}. "
                    f"Попытка {retries + 1}/{MAX_RETRIES}."
                )
        except Exception as e:
            logger.error(
                f"Ошибка при отправке batch-запроса: {e}. Попытка {retries + 1}/{MAX_RETRIES}."
            )
        retries += 1
        time.sleep(RETRY_DELAY)

    logger.error("Не удалось отправить batch-запрос после всех попыток.")
    raise Exception("Не удалось отправить batch-запрос к ScraperAPI.")


def check_batch_status_from_file(batch_file_path="json_product/batch_request.json"):
    """
    Читает batch-файл и проверяет статус заданий.
    """
    batch_file = Path(batch_file_path)
    if not batch_file.exists():
        logger.error(f"Файл {batch_file} не найден.")
        return {}

    with open(batch_file, "r", encoding="utf-8") as f:
        batch_data = json.load(f)

    status_urls = [job["statusUrl"] for job in batch_data]
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
                id_product = urllib.parse.parse_qs(
                    urllib.parse.urlparse(original_url).query
                )["q"][0]
                json_file = json_product_directory / f"{id_product}.json"

                if status == "finished":
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
    batch_response = submit_batch_jobs(product_ids)
    if not batch_response:
        return {}

    results = check_batch_status_from_file()
    return results


if __name__ == "__main__":
    product_ids = ["5802243444"]
    json_product_directory.mkdir(parents=True, exist_ok=True)
    results = get_pages_html_batch(product_ids)

    # Проверяем, все ли продукты успешно загружены
    all_successful = all(result is not None for result in results.values())

    for product_id, result in results.items():
        if result:
            logger.info(f"Успешно загружен {product_id}")
        else:
            logger.error(f"Ошибка загрузки {product_id}")

    # Удаляем batch_request.json, если все успешно
    batch_file = json_product_directory / "batch_request.json"
    if all_successful and batch_file.exists():
        batch_file.unlink()
        logger.info(f"Файл {batch_file} удален после успешной загрузки всех продуктов.")
    elif not all_successful:
        logger.warning(
            "Не все продукты загружены успешно. Файл batch_request.json сохранен для повторной попытки."
        )
