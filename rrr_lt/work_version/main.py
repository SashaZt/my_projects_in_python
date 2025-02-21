import asyncio
import os
import re
import sys
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger

# Парсинг товаров
from database import export_to_excel

# Скачивание товаров
from main_th import process_products_with_threads

# Скачивание кодов запчастей
from main_th_queue import process_pages_with_threads_code

current_directory = Path.cwd()
html_code_directory = current_directory / "html_code"
json_product_directory = current_directory / "json_product"
log_directory = current_directory / "log"
config_directory = current_directory / "config"
data_directory = current_directory / "data"
config_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
json_product_directory.mkdir(parents=True, exist_ok=True)
html_code_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
xlsx_result = data_directory / "result.xlsx"
output_csv_file = data_directory / "output.csv"
env_file_path = config_directory / ".env"
config_file_path = config_directory / "config.txt"

load_dotenv(env_file_path)
API_KEY = os.getenv("API_KEY")
MAX_RETRIES = int(os.getenv("MAX_RETRIES"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY"))
TOTAL_PAGES = int(os.getenv("TOTAL_PAGES"))
NUM_THREADS = int(os.getenv("NUM_THREADS"))

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


def read_urls(csv_path):
    """Читает CSV-файл и возвращает список URL."""
    try:
        df = pd.read_csv(csv_path, usecols=["code"])  # Загружаем только колонку "url"
        return (
            df["code"].dropna().tolist()
        )  # Убираем пустые значения и возвращаем список
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        return []


def extract_data_code():
    all_data = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_code_directory.glob("*.html"):
        with open(html_file, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        code_tag = soup.find_all("button", attrs={"data-testid": "part-code"})
        if not code_tag:
            logger.error(f"Не найден код в файле {html_file}")
            continue
        for code in code_tag:
            code_text = code.text.strip()  # Убираем лишние пробелы
            all_data.append(code_text)
    save_code_csv(all_data)


def save_code_csv(data):
    # Создаем DataFrame с заголовком "code"
    df = pd.DataFrame(data, columns=["code"])

    # Сохраняем в CSV файл
    output_file = output_csv_file  # Можно изменить путь и имя файла
    df.to_csv(output_file, index=False, encoding="utf-8")
    logger.info(
        f"Все коды успешно сохранены в {output_file}. Всего записей: {len(data)}"
    )


def main_config():
    # Парсим данные из файла
    headers, cookies = parse_curl_from_file()

    # Фильтруем только нужные ключи
    filtered_headers, filtered_cookies = filter_required_data(headers, cookies)

    return filtered_headers, filtered_cookies


def parse_curl_from_file():
    # Читаем файл config.txt
    with open(config_file_path, "r", encoding="utf-8") as f:
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


def main_loop():
    while True:
        print(
            "\nВыберите действие:\n"
            "1. Скачивание кодов с сайта\n"
            "2. Извлечение кодов запчастей\n"
            "3. Скачивание запчастей\n"
            "4. Получение файлов Ексель\n"
            "5. Удалить временные файлы\n"
            "0. Выход"
        )
        choice = input("Введите номер действия: ")
        if choice == "1":
            process_pages_with_threads_code(
                total_pages=TOTAL_PAGES,
                num_threads=NUM_THREADS,
                api_key=API_KEY,
                html_code_directory=html_code_directory,
                max_retries=MAX_RETRIES,
                delay=RETRY_DELAY,
            )

        elif choice == "2":
            # извлечь_кодов запчастей
            extract_data_code()

        elif choice == "3":
            urls = read_urls(output_csv_file)
            headers, cookies = main_config()
            process_products_with_threads(
                id_products=urls,
                num_threads=NUM_THREADS,
                api_key=API_KEY,
                base_url="https://rrr.lt/ru/poisk",
                headers=headers,
                cookies=cookies,
                json_product_directory=json_product_directory,
                max_retries=MAX_RETRIES,
                delay=RETRY_DELAY,
            )
        elif choice == "4":
            # Получить данные о продукте
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(export_to_excel())
            loop.close()
        elif choice == "5":
            for file in html_code_directory.glob("*.html"):
                file.unlink()
            for file in json_product_directory.glob("*.json"):
                file.unlink()
            print("Временные файлы удалены")
        elif choice == "0":
            break
        else:
            print("Неверный ввод. Попробуйте еще раз.")


if __name__ == "__main__":
    main_loop()
