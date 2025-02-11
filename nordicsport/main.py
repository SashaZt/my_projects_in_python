import csv
import hashlib
import json
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import gspread
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger
from oauth2client.service_account import ServiceAccountCredentials

env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)

SPREADSHEET = os.getenv("SPREADSHEET")
SHEET = os.getenv("SHEET")
time_a = os.getenv("TIME_A")
time_b = os.getenv("TIME_B")
BATCH_SIZE = os.getenv("BATCH_SIZE")
PAUSE_DURATION = os.getenv("PAUSE_DURATION")

current_directory = Path.cwd()
data_directory = current_directory / "data"
html_directory = current_directory / "html"
log_directory = current_directory / "log"
configuration_directory = current_directory / "configuration"
service_account_file = configuration_directory / "credentials.json"
log_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

output_json_file = data_directory / "output.json"
output_csv_file = data_directory / "output.csv"
output_xml_file = data_directory / "output.xml"
log_file_path = log_directory / "log_message.log"

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
cookies = {
    "secure_customer_sig": "",
    "localization": "UA",
    "cart_currency": "EUR",
    "_shopify_y": "E717B01C-0604-4E6E-b4a4-a2cf8e0db410",
    "_tracking_consent": "%7B%22con%22%3A%7B%22CMP%22%3A%7B%22a%22%3A%22%22%2C%22m%22%3A%22%22%2C%22p%22%3A%22%22%2C%22s%22%3A%22%22%7D%7D%2C%22v%22%3A%222.1%22%2C%22region%22%3A%22UA18%22%2C%22reg%22%3A%22%22%2C%22purposes%22%3A%7B%22a%22%3Atrue%2C%22p%22%3Atrue%2C%22m%22%3Atrue%2C%22t%22%3Atrue%7D%2C%22display_banner%22%3Afalse%2C%22sale_of_data_region%22%3Afalse%2C%22consent_id%22%3A%222B8B1ACA-52ad-4A74-a4ca-f851092e7cd7%22%7D",
    "_orig_referrer": "",
    "_landing_page": "%2F",
    "locale_bar_accepted": "1",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    # 'cookie': 'secure_customer_sig=; localization=UA; cart_currency=EUR; _shopify_y=E717B01C-0604-4E6E-b4a4-a2cf8e0db410; _tracking_consent=%7B%22con%22%3A%7B%22CMP%22%3A%7B%22a%22%3A%22%22%2C%22m%22%3A%22%22%2C%22p%22%3A%22%22%2C%22s%22%3A%22%22%7D%7D%2C%22v%22%3A%222.1%22%2C%22region%22%3A%22UA18%22%2C%22reg%22%3A%22%22%2C%22purposes%22%3A%7B%22a%22%3Atrue%2C%22p%22%3Atrue%2C%22m%22%3Atrue%2C%22t%22%3Atrue%7D%2C%22display_banner%22%3Afalse%2C%22sale_of_data_region%22%3Afalse%2C%22consent_id%22%3A%222B8B1ACA-52ad-4A74-a4ca-f851092e7cd7%22%7D; _orig_referrer=; _landing_page=%2F; locale_bar_accepted=1',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
}


def get_google_sheet():
    """Подключается к Google Sheets и возвращает указанный лист."""
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            service_account_file, scope
        )
        client = gspread.authorize(creds)

        # Открываем таблицу по ключу и возвращаем лист
        spreadsheet = client.open_by_key(SPREADSHEET)
        logger.info("Успешное подключение к Google Spreadsheet.")
        return spreadsheet.worksheet(SHEET)
    except FileNotFoundError:
        raise FileNotFoundError("Файл credentials.json не найден. Проверьте путь.")
    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        raise
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        raise


# Получение листа Google Sheets
sheet = get_google_sheet()


def download_xml():
    if os.path.exists(html_directory):
        shutil.rmtree(html_directory)
    response = requests.get(
        "https://nordicsport.com/sitemap_products_1.xml?from=1447756726390&to=14706192122188",
        cookies=cookies,
        headers=headers,
        timeout=30,
    )

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(output_xml_file, "wb") as file:
            file.write(response.content)
        logger.info(f"Файл успешно сохранен в: {output_xml_file}")
    else:
        logger.error(f"Ошибка при скачивании файла: {response.status_code}")


def parsin_xml():
    download_xml()

    # Чтение XML файла
    with open(output_xml_file, "r", encoding="utf-8") as file:
        xml_content = file.read()

    # Определяем пространства имен
    namespaces = {
        "ns": "http://www.sitemaps.org/schemas/sitemap/0.9",
        "image": "http://www.google.com/schemas/sitemap-image/1.1",
    }

    # Парсим XML из строки
    root = ET.fromstring(xml_content)

    product_urls = []

    # Ищем все теги <loc> и фильтруем только ссылки на продукты
    for url in root.findall("ns:url", namespaces):
        loc = url.find("ns:loc", namespaces)
        if loc is not None:
            url_text = loc.text
            if "/products/" in url_text:
                product_urls.append(url_text)

    # Убираем дубликаты
    unique_urls = list(set(product_urls))

    # Сохраняем в CSV
    url_data = pd.DataFrame(unique_urls, columns=["url"])
    url_data.to_csv(output_csv_file, index=False)

    logger.info(f"Найдено {len(unique_urls)} уникальных ссылок на продукты.")


def fetch(url):
    response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def get_html(url, html_file):
    src = fetch(url)
    with open(html_file, "w", encoding="utf-8") as file:
        file.write(src)
    logger.info(html_file)
    # time.sleep(5)


def main_th():
    if not os.path.exists(html_directory):
        html_directory.mkdir(parents=True, exist_ok=True)
    urls = []
    with open(output_csv_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            urls.append(row["url"])

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for url in urls:
            output_html_file = (
                html_directory / f"html_{hashlib.md5(url.encode()).hexdigest()}.html"
            )

            if not os.path.exists(output_html_file):
                futures.append(executor.submit(get_html, url, output_html_file))
            else:
                logger.info(f"Файл для {url} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            # Здесь вы можете обрабатывать результаты по мере их завершения
            results.append(future.result())


def pars_htmls():
    logger.info("Собираем данные со страниц html")
    all_data = []

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        # Поиск скрипта с типом application/ld+json и типом Product
        product_script = soup.find(
            "script",
            type="application/ld+json",
            string=lambda text: text and '"@type": "Product"' in text,
        )

        if product_script:
            try:
                product_data = json.loads(product_script.string)

                name = product_data.get("name")
                sku = product_data.get("sku")

                offers = product_data.get("offers", [])
                price = None

                if isinstance(offers, list) and offers:
                    raw_price = offers[0].get("price")
                    if raw_price:
                        price = raw_price.replace(".", ",")
                elif isinstance(offers, dict):
                    raw_price = offers.get("price")
                    if raw_price:
                        price = raw_price.replace(".", ",")

                data_json = {"name": name, "sku": sku, "price": price}
                all_data.append(data_json)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                return None
        else:
            logger.error("Product JSON не найден.")
            return None

    logger.info(all_data)
    update_sheet_with_data(sheet, all_data)


def ensure_row_limit(sheet, required_rows=8000):
    """Увеличивает количество строк в листе Google Sheets, если их меньше требуемого количества."""
    current_rows = len(sheet.get_all_values())
    if current_rows < required_rows:
        sheet.add_rows(required_rows - current_rows)


ensure_row_limit(sheet, 1000)


def update_sheet_with_data(sheet, data, total_rows=8000):
    """Записывает данные в указанные столбцы листа Google Sheets с использованием пакетного обновления."""
    if not data:
        raise ValueError("Данные для обновления отсутствуют.")

    # Заголовки из ключей словаря
    headers = list(data[0].keys())

    # Запись заголовков в первую строку
    sheet.update(values=[headers], range_name="A1", value_input_option="RAW")

    # Формирование строк для записи
    rows = [[entry.get(header, "") for header in headers] for entry in data]

    # Добавление пустых строк до общего количества total_rows
    if len(rows) < total_rows:
        empty_row = [""] * len(headers)
        rows.extend([empty_row] * (total_rows - len(rows)))

    # Определение диапазона для записи данных
    end_col = chr(65 + len(headers) - 1)  # Преобразование индекса в букву (A, B, C...)
    range_name = f"A2:{end_col}{total_rows + 1}"

    # Запись данных в лист
    sheet.update(values=rows, range_name=range_name, value_input_option="USER_ENTERED")


if __name__ == "__main__":
    parsin_xml()
    main_th()
    pars_htmls()
