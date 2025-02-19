import asyncio
import json
from pathlib import Path
from typing import Optional, Dict
import random
import logging
import pandas as pd
import json
import time
import urllib.parse
import requests
import time
from urllib.parse import urlparse, urlunparse
import sys
import pandas as pd
import requests
from loguru import logger
from pathlib import Path
from bs4 import BeautifulSoup



API_KEY = "6c54502fd688c7ce737f1c650444884a"
# API_KEY = "b7141d2b54426945a9f0bf6ab4c7bc54"
# Настройте максимальное количество попыток, если требуется
MAX_RETRIES = 10
RETRY_DELAY = 30  # Задержка между попытками в секундах



current_directory = Path.cwd()
html_directory = current_directory / "html"
json_directory = current_directory / "json"
log_directory = current_directory / "log"
data_directory = current_directory / "data"
log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)

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
def make_request_with_retries(url, params, max_retries=10, delay=30, headers=None):
    """
    Делает запрос с повторными попытками.

    Args:
        url (str): URL для запроса.
        params (dict): Параметры запроса.
        max_retries (int): Максимальное количество попыток.
        delay (int): Задержка между попытками в секундах.
        headers (dict): Пользовательские заголовки.

    Returns:
        Response | None: Успешный ответ или None, если все попытки исчерпаны.
    """
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, params=params, headers=headers, timeout=60)
            if response.status_code == 200:
                return response
            else:
                logger.warning(
                    f"Ошибка {response.status_code} при запросе {url}. Попытка {retries + 1}/{max_retries}."
                )
        except Exception as e:
            logger.error(
                f"Ошибка при выполнении запроса: {e}. Попытка {retries + 1}/{max_retries}."
            )
        retries += 1
        time.sleep(delay)

    logger.error(f"Не удалось выполнить запрос после {max_retries} попыток: {url}")
    
    return None

def get_all_page_html(id_product):
    url = f"https://rrr.lt/ru/poisk"
    
    # Определяем необходимые заголовки
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'ru,en;q=0.9,uk;q=0.8',
        'x-requested-with': 'XMLHttpRequest'
    }
    
    # Параметры запроса
    query_params = {
        'q': id_product,
        'prs': '2',
        'page': '1'
    }
    
    # Параметры для ScraperAPI
    payload = {
        "api_key": API_KEY,
        "url": url,
        "keep_headers": "true",  # Важно для сохранения пользовательских заголовков
        # 'render': 'true'  # Включаем рендеринг JavaScript
    }
    json_file = json_directory / f"{id_product}.json"
    if json_file.exists():
        logger.info(f"Файл {json_file} уже существует. Пропускаем.")
        return
    # Добавляем параметры запроса к URL
    payload["url"] = f"{url}?{urllib.parse.urlencode(query_params)}"

    response = make_request_with_retries(
        "https://api.scraperapi.com/", 
        payload, 
        MAX_RETRIES, 
        RETRY_DELAY,
        headers=headers  # Передаем заголовки в функцию
    )
    
    if not response:
        raise Exception(
            "Не удалось загрузить первую страницу после нескольких попыток."
        )
        
    
    src = response.text
    with open(json_file, "w", encoding="utf-8") as file:
        file.write(src)

    logger.info(f"Скачано {json_file}")



def read_urls(csv_path):
    """Читает CSV-файл и возвращает список URL."""
    try:
        df = pd.read_csv(csv_path, usecols=["id"])  # Загружаем только колонку "url"
        return df["url"].dropna().tolist()  # Убираем пустые значения и возвращаем список
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        return []
# def extract_data():
#     all_data = []
    
#     for json_file in json_directory.glob("*.json"):
#         with open(json_file, "r", encoding="utf-8") as file:
#             data = json.load(file)
#         logger.info(f"Обработка файла: {json_file}")
#         # Найти деталь "Охладитель EGR" с минимальной ценой
#         parts = data.get("parts", [])
#         if not parts:
#             logger.error("Не найдены детали в JSON.")
#             continue
#         min_price_part = min(
#             parts,
#             key=lambda x: float(x.get("price", float("inf"))),
#             default=None
#         )
#         sku = data.get("search_query", None)
        
#         # Найти категорию "Система выброса газов" с part_count > 0
#         categories = data.get("categories", {})
#         category_name = next(
#             (category["name"] for category in categories.values() if category.get("part_count", 0) > 0),
#             None
#         )
        
#         if min_price_part and category_name:
#             delivery_price_str = min_price_part.get("delivery_price", None).replace(" €", "")
#             price_str = min_price_part["price"]
#             # Если значение отсутствует (None) или пустое, устанавливаем "0"
#             if not delivery_price_str:
#                 delivery_price_str = "0"
#             else:
#                 delivery_price_str = delivery_price_str.replace(" €", "")

#             if not price_str:
#                 price_str = "0"

#             # Преобразуем строки в числа типа float и суммируем
#             delivery_price = float(delivery_price_str)
#             price = float(price_str)
#             result = {
#                 "Бренд": min_price_part.get("car", {}).get("manufacturer", None),
#                 "Код": sku,
#                 "Kод производителя": data.get("manufacturer_code", None),
#                 "Описание": f"{category_name} | Оригінал | Гарантія  на весь товар | Гарантійне встановлення запчастини у нас в СТО | Запчастини з Євро-розборів | Відповідальність | Телефонуйте | Мирного дня.",
#                 "Цена товара и доставки": delivery_price + price,
#                 "Цена товара": price,
#                 "Цена только доставки": delivery_price,
#                 "Количество, ШТ.": "1",
#                 "Б/У": "1",
#                 "Фото товара": None,
#                 # "part_name": min_price_part["part_name"],
                
                
#             }
#             logger.info(f"Найдены данные: {result}")
#             all_data.append(result)
#     if all_data:
#         df = pd.DataFrame(all_data)
#         df.to_excel(xlsx_result, index=False)
#         logger.info(f"Данные успешно сохранены в файл {xlsx_result}")
def extract_data():
    # Словарь для хранения данных по категориям
    category_data = {}
    
    for json_file in json_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        logger.info(f"Обработка файла: {json_file}")
        
        parts = data.get("parts", [])
        if not parts:
            logger.error("Не найдены детали в JSON.")
            continue
            
        min_price_part = min(
            parts,
            key=lambda x: float(x.get("price", float("inf"))),
            default=None
        )
        sku = data.get("search_query", None)
        
        categories = data.get("categories", {})
        category_name = next(
            (category["name"] for category in categories.values() if category.get("part_count", 0) > 0),
            None
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
                "Код": sku,
                "Kод производителя": manufacturer_code,
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
            safe_category_name = "".join(c for c in category_name if c.isalnum() or c in (' ', '-', '_'))
            file_name = f"{safe_category_name}.xlsx"
            df = pd.DataFrame(data)
            df.to_excel(file_name, index=False)
            logger.info(f"Создан файл для категории '{category_name}': {file_name}")



if __name__ == "__main__":
    # urls = read_urls(output_csv_file)
    # for url in urls[:1]:
    #     url = "19070006031"
    #     get_all_page_html(url)
    extract_data()