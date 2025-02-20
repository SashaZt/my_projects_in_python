import json
import sys
import time
import urllib.parse
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger

from config import COOKIES, HEADERS
from main_th import process_products_with_threads
from main_th_queue import process_pages_with_threads_code
from scrap_product import extract_data_product

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


API_KEY = "6c54502fd688c7ce737f1c650444884a"
# API_KEY = "b7141d2b54426945a9f0bf6ab4c7bc54"
# Настройте максимальное количество попыток, если требуется
MAX_RETRIES = 10
RETRY_DELAY = 30  # Задержка между попытками в секундах
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


# # Скачиваем коды товаров
# process_pages_with_threads_code(
#     total_pages=3,
#     num_threads=50,
#     api_key=API_KEY,
#     html_code_directory=html_code_directory,
#     max_retries=MAX_RETRIES,
#     delay=RETRY_DELAY,
# )


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


# # Запуск скачивания страниц с товарами
# urls = read_urls(output_csv_file)
# process_products_with_threads(
#     id_products=urls,
#     num_threads=10,
#     api_key=API_KEY,
#     base_url="https://rrr.lt/ru/poisk",
#     headers=HEADERS,
#     cookies=COOKIES,
#     json_product_directory=json_product_directory,
#     max_retries=MAX_RETRIES,
#     delay=RETRY_DELAY,
# )
if __name__ == "__main__":
    extract_data_product()
