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
from main_th_queue import process_pages_with_threads_code

# from main_th import process_products_with_threads

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


def extract_data_product():
    # Словарь для хранения данных по категориям
    category_data = {}

    for json_file in json_product_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        logger.info(f"Обработка файла: {json_file}")

        parts = data.get("parts", [])
        if not parts:
            logger.error("Не найдены детали в JSON.")
            continue

        min_price_part = min(
            parts, key=lambda x: float(x.get("price", float("inf"))), default=None
        )
        sku = data.get("search_query", None)

        categories = data.get("categories", {})
        category_name = next(
            (
                category["name"]
                for category in categories.values()
                if category.get("part_count", 0) > 0
            ),
            None,
        )

        if min_price_part and category_name:
            manufacturer_code = min_price_part.get("manufacturer_code", None)
            if not manufacturer_code:
                continue
            delivery_price_str = min_price_part.get("delivery_price", None)
            if delivery_price_str:
                delivery_price_str = delivery_price_str.replace(" €", "")
            else:
                delivery_price_str = "0"

            price_str = min_price_part.get("price", "0")
            if not price_str:
                price_str = "0"

            delivery_price = float(delivery_price_str)
            price = float(price_str)

            result = {
                "Бренд": min_price_part.get("car", {}).get("manufacturer", None),
                "Код": manufacturer_code,
                # "Kод производителя": manufacturer_code,
                "Описание": f"{category_name} | Оригінал | Гарантія  на весь товар | Гарантійне встановлення запчастини у нас в СТО | Запчастини з Євро-розборів | Відповідальність | Телефонуйте | Мирного дня.",
                "Цена товара и доставки": delivery_price + price,
                "Цена товара": price,
                "Цена только доставки": delivery_price,
                "Количество, ШТ.": "1",
                "Б/У": "1",
                "Фото товара": None,
            }

            # Добавляем данные в соответствующую категорию
            if category_name not in category_data:
                category_data[category_name] = []
            category_data[category_name].append(result)
            logger.info(f"Добавлены данные в категорию {category_name}")

    # Сохраняем данные в отдельные файлы по категориям
    for category_name, data in category_data.items():
        if data:
            # Создаем безопасное имя файла, заменяя недопустимые символы
            safe_category_name = "".join(
                c for c in category_name if c.isalnum() or c in (" ", "-", "_")
            )

            file_name = data_directory / f"{safe_category_name}.xlsx"
            df = pd.DataFrame(data)
            df.to_excel(file_name, index=False)
            logger.info(f"Создан файл для категории '{category_name}': {file_name}")
