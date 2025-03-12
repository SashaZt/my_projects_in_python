import csv
import hashlib
import json
import os
import re
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
from config.logger import logger
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

current_directory = Path.cwd()
config_directory = current_directory / "config"
data_directory = current_directory / "data"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
# output_xml_file = data_directory / "output.xml"
output_csv_file = data_directory / "output.csv"
output_csv_file = data_directory / "output.csv"
config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"

cookies = {
    "WELLSESSID": "cat8ii70qffcs5ss0eiese6gak",
    "_gcl_au": "1.1.1815884540.1741706393",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    # 'cookie': 'WELLSESSID=cat8ii70qffcs5ss0eiese6gak; _gcl_au=1.1.1815884540.1741706393',
}


def get_config():
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


config = get_config()
SPREADSHEET = config["google"]["spreadsheet"]
SHEET = config["google"]["sheet"]


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
    for page in range(1, 3):
        response = requests.get(
            f"https://homegarden.com.pl/sitemap.products.{page}.xml",
            cookies=cookies,
            headers=headers,
            timeout=30,
        )
        output_xml_file = data_directory / f"output_{page}.xml"
        # Проверка успешности запроса
        if response.status_code == 200:
            # Сохранение содержимого в файл
            with open(output_xml_file, "wb") as file:
                file.write(response.content)
            logger.info(f"Файл успешно сохранен в: {output_xml_file}")
        else:
            logger.error(f"Ошибка при скачивании файла: {response.status_code}")


def parse_sitemap():
    download_xml()
    try:
        urls = []
        for page in range(1, 3):
            output_xml_file = data_directory / f"output_{page}.xml"
            # Чтение XML файла
            with open(output_xml_file, "r", encoding="utf-8") as file:
                xml_content = file.read()

            # Парсинг XML
            root = ET.fromstring(xml_content)

            # Регистрация пространств имен
            namespaces = {
                "ns": "http://www.sitemaps.org/schemas/sitemap/0.9",
                "image": "http://www.google.com/schemas/sitemap-image/1.1",
            }

            # Извлечение только URL из тегов loc, непосредственно внутри url
            # Важно: используем XPath, который выбирает только прямые дочерние элементы loc тега url
            # ./ns:loc - выбирает только прямые loc теги, игнорируя image:loc
            urls = []

            for url_elem in root.findall(".//ns:url", namespaces):
                loc_elem = url_elem.find("./ns:loc", namespaces)
                if loc_elem is not None and loc_elem.text:
                    url = loc_elem.text.strip()
                    urls.append(url)

            # Вывод количества найденных URL
            logger.info(f"Найдено {len(urls)} URL, соответствующих шаблону")

            # Сохранение в CSV
            url_data = pd.DataFrame(urls, columns=["url"])
            url_data.to_csv(output_csv_file, index=False)
            logger.info(f"URL адреса сохранены в {output_csv_file}")

            return urls

    except FileNotFoundError:
        logger.error(f"Ошибка: Файл {output_xml_file} не найден")
        return []
    except ET.ParseError as e:
        logger.error(f"Ошибка при парсинге XML: {e}")
        return []
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return []


def main_th():
    if not os.path.exists(html_directory):
        html_directory.mkdir(parents=True, exist_ok=True)
    urls = []
    with open(output_csv_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            urls.append(row["url"])

    with ThreadPoolExecutor(max_workers=20) as executor:
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


def fetch(url):
    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)

        # Проверка статуса ответа
        if response.status_code != 200:
            logger.warning(
                f"Статус не 200 для {url}. Получен статус: {response.status_code}. Пропускаем."
            )
            return None

        return response.text

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при загрузке {url}: {str(e)}")
        return None


def get_html(url, html_file):
    src = fetch(url)

    if src is None:
        return url, html_file, False

    with open(html_file, "w", encoding="utf-8") as file:
        file.write(src)

    logger.info(f"Успешно загружен и сохранен: {html_file}")
    return url, html_file, True


def ensure_row_limit(sheet, required_rows=10000):
    """Увеличивает количество строк в листе Google Sheets, если их меньше требуемого количества."""
    current_rows = len(sheet.get_all_values())
    if current_rows < required_rows:
        sheet.add_rows(required_rows - current_rows)


def extract_product_data(product_json):
    """
    Извлекает данные продукта из JSON структуры

    Args:
        product_json (dict): JSON структура продукта

    Returns:
        dict: Извлеченные данные продукта
    """
    try:
        product_name = product_json.get("name")
        sku = product_json.get("sku")

        # Извлекаем данные из offers
        offers = product_json.get("offers", {})
        offer_price = offers.get("price")
        if offer_price:
            offer_price = str(offer_price).replace(".", ",")
        availability = offers.get("availability")
        schema_terms = (
            r"(InStock|Discontinued|BackOrder|OutOfStock)"  # Шаблон для поиска
        )
        all_availability = {
            "Discontinued": "Припинено",
            "BackOrder": "Зворотне замовлення",
            "InStock": "В наявності",
            "OutOfStock": "Немає в наявності",
        }

        matches = re.findall(schema_terms, availability or "")  # Проверяем на None

        if matches:
            last_term = matches[-1]
            result_availability = all_availability[last_term]
        data_json = {
            "Назва": product_name,
            "Код товару(HG-)": f"HG-{sku}",
            "Ціна": offer_price,
            "Наявність": result_availability,
        }
        return data_json
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных продукта: {e}")
        return None


def sanitize_json(json_str):
    # Удаляем управляющие символы
    json_str = re.sub(r"[\x00-\x1F\x7F]", "", json_str)

    # Корректируем HTML-сущности
    json_str = json_str.replace("&amp;", "&")
    json_str = json_str.replace("&nbsp;", " ")
    json_str = json_str.replace("&times;", "x")
    json_str = json_str.replace("&quot;", '"')
    json_str = json_str.replace("&#39;", "'")

    return json_str


def pars_htmls():
    logger.info("Собираем данные со страниц html")
    all_data = []

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()
        # logger.debug(html_file)
        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        # Находим все скрипты с типом application/ld+json
        scripts = soup.find_all("script", type="application/ld+json")

        if not scripts:
            logger.warning(
                f"В файле {html_file.name} не найдено скриптов с типом application/ld+json"
            )
            continue

        # Флаг для отслеживания, был ли найден продукт
        product_found = False

        # Перебираем все скрипты JSON-LD
        for script in scripts:
            try:
                # Получаем текст скрипта и проверяем его наличие
                script_text = script.string
                if not script_text or not script_text.strip():
                    continue
                # Очищаем JSON от проблемных символов
                script_text = sanitize_json(script_text)

                # Парсим JSON
                json_data = json.loads(script_text)

                # Проверяем, является ли это продуктом
                if isinstance(json_data, dict) and json_data.get("@type") == "Product":
                    # logger.info("Найдена структура Product JSON-LD")
                    product_found = True

                    # Извлекаем данные основного продукта
                    main_product = extract_product_data(json_data)
                    if main_product:
                        all_data.append(main_product)

                    break
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                # Или можно использовать print:
                logger.info(f"Ошибка парсинга JSON: {e}")
        else:
            logger.error("Product JSON не найден.")
    update_sheet_with_data(sheet, all_data)


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
    parse_sitemap()
    main_th()
    pars_htmls()
