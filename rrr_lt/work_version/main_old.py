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


def make_request_page_html(url, params, max_retries=10, delay=30, headers=None):
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


def get_page_html(id_product):
    url = "https://rrr.lt/ru/poisk"
    headers, cookies = main_config()
    # Параметры запроса
    query_params = {"q": id_product, "prs": "2", "page": "1"}

    # Параметры для ScraperAPI
    payload = {
        "api_key": API_KEY,
        "url": url,
        "keep_headers": "true",  # Важно для сохранения пользовательских заголовков
    }
    json_file = json_product_directory / f"{id_product}.json"
    if json_file.exists():
        logger.info(f"Файл {json_file} уже существует. Пропускаем.")
        return
    # Добавляем параметры запроса к URL
    payload["url"] = f"{url}?{urllib.parse.urlencode(query_params)}"
    # Формируем строку Cookie из словаря cookies
    cookie_string = "; ".join(f"{key}={value}" for key, value in cookies.items())
    headers["Cookie"] = cookie_string
    response = make_request_page_html(
        "https://api.scraperapi.com/",
        payload,
        MAX_RETRIES,
        RETRY_DELAY,
        headers=headers,  # Передаем заголовки в функцию
    )

    if not response:
        raise Exception(
            "Не удалось загрузить первую страницу после нескольких попыток."
        )

    src = response.text
    with open(json_file, "w", encoding="utf-8") as file:
        file.write(src)

    logger.info(f"Скачано {json_file}")


def make_request_code(url, params, max_retries=10, delay=30, headers=None):
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
            logger.info(f"response.status_code: {response.status_code}")
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


def get_all_code(pages):
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "x-requested-with": "XMLHttpRequest",
    }
    # Параметры для ScraperAPI
    payload = {
        "api_key": API_KEY,
        "keep_headers": "true",  # Важно для сохранения пользовательских заголовков
        # 'render': 'true'  # Включаем рендеринг JavaScript
    }
    for page in range(0, pages + 1):
        if page == 0:
            url = "https://rrr.lt/ru/spisok-kodov-zapasnykh-chastey"
            # Добавляем параметры запроса к URL
            payload["url"] = f"{url}"
        else:
            url = f"https://rrr.lt/ru/spisok-kodov-zapasnykh-chastey?page={page}"
            params = {
                "page": page,
            }
            # Добавляем параметры запроса к URL
            payload["url"] = f"{url}?{urllib.parse.urlencode(params)}"

        # Определяем необходимые заголовки

        html_file = html_code_directory / f"page_{page}.html"
        if html_file.exists():
            logger.info(f"Файл {html_file} уже существует. Пропускаем.")
            continue

        response = make_request_code(
            "https://api.scraperapi.com/",
            payload,
            MAX_RETRIES,
            RETRY_DELAY,
            headers=headers,  # Передаем заголовки в функцию
        )

        if not response:
            raise Exception(
                "Не удалось загрузить первую страницу после нескольких попыток."
            )

        src = response.text
        with open(html_file, "w", encoding="utf-8") as file:
            file.write(src)

        logger.info(f"Скачано {html_file}")


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
            safe_category_name = "".join(
                c for c in category_name if c.isalnum() or c in (" ", "-", "_")
            )

            file_name = data_directory / f"{safe_category_name}.xlsx"
            df = pd.DataFrame(data)
            df.to_excel(file_name, index=False)
            logger.info(f"Создан файл для категории '{category_name}': {file_name}")


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


def main_config():
    # Парсим данные из файла
    headers, cookies = parse_curl_from_file("config.txt")

    # Фильтруем только нужные ключи
    filtered_headers, filtered_cookies = filter_required_data(headers, cookies)

    return filtered_headers, filtered_cookies


if __name__ == "__main__":
    # # Получить все коды запчастей
    # get_all_code(3)
    # # # Получить все коды запчастей
    # extract_data_code()
    # Получить данные о продукте
    urls = read_urls(output_csv_file)
    for url in urls[:1]:
        get_all_page_html(url)
    # Получить данные о продукте
    # extract_data_product()
