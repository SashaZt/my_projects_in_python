import json
import sys
import time
import urllib.parse
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from config import COOKIES, HEADERS
from loguru import logger
from main_th import process_products_with_threads

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


urls = read_urls(output_csv_file)
# id_products = ["5802243444", "7355163422"]  # Список ID продуктов
process_products_with_threads(
    id_products=urls,
    num_threads=10,
    api_key=API_KEY,
    base_url="https://rrr.lt/ru/poisk",
    headers=HEADERS,
    cookies=COOKIES,
    json_product_directory=json_product_directory,
    max_retries=MAX_RETRIES,
    delay=RETRY_DELAY,
)
