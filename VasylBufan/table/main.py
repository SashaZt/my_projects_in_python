import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import gspread
import pandas as pd
import requests
from google.oauth2.service_account import Credentials
from loguru import logger
from lxml import etree

current_directory = Path.cwd()
xml_directory = current_directory / "xml"
log_directory = current_directory / "log"
config_directory = current_directory / "config"

config_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"
config_file_path = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"

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


def load_json_data(file_path):
    """Загрузка данных из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из {file_path}: {e}")
        return None


def save_json_data(data, file_path):
    """Сохранение данных в JSON файл"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {file_path}: {e}")
        return False


config = load_json_data(config_file_path)
URLS = config.get("competitor_www", [])
MY_URL = config.get("my_www")
HEADERS = config.get("headers", {})
SPREADSHEET = config["google"]["spreadsheet"]
SHEET = config["google"]["sheet"]


def get_google_sheet(sheet_one):
    """Подключается к Google Sheets и возвращает указанный лист."""
    try:
        # Новый способ аутентификации с google-auth
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )

        # Авторизация в gspread с новыми учетными данными
        client = gspread.authorize(credentials)

        # Открываем таблицу по ключу и возвращаем лист
        spreadsheet = client.open_by_key(SPREADSHEET)
        logger.info("Успешное подключение к Google Spreadsheet.")
        return spreadsheet.worksheet(sheet_one)
    except FileNotFoundError:
        logger.error("Файл учетных данных не найден. Проверьте путь.")
        raise FileNotFoundError("Файл учетных данных не найден. Проверьте путь.")
    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        raise
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        raise


def update_sheet_with_data(sheet, data, total_rows=10000):
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
    logger.info(f"Обновлено {len(data)} строк в Google Sheets")


def download_xml(url, headers):
    """
    Скачивает XML файл по указанному URL.

    Args:
        url (str): URL для скачивания XML файла
        headers (dict): Заголовки для HTTP запроса
        xml_dir (Path, optional): Директория для сохранения файлов. По умолчанию xml_directory.

    Returns:
        Path or None: Путь к сохраненному файлу или None в случае ошибки
    """
    try:
        # Извлечение имени файла из URL
        filename = urlparse(url).path.split("/")[-1]

        # Если имя файла пустое, используем домен
        if not filename:
            filename = urlparse(url).netloc.replace(".", "_")

        # Добавляем расширение .xml если его нет
        if not filename.endswith(".xml"):
            xml_file_path = xml_directory / f"{filename}.xml"
        else:
            xml_file_path = xml_directory / filename

        logger.info(f"Скачиваем XML файл: {url}")

        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

        # Проверка успешности запроса
        if response.status_code == 200:
            # Сохранение содержимого в файл
            with open(xml_file_path, "wb") as file:
                file.write(response.content)
            logger.info(f"Файл успешно сохранен в: {xml_file_path}")
            return xml_file_path
        else:
            logger.error(f"Ошибка при скачивании файла: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Исключение при скачивании файла {url}: {e}")
        return None


def download_all_xml_files():
    """
    Скачивает все XML файлы на основе конфигурации.

    Args:
        config_file_path (str): Путь к файлу конфигурации

    Returns:
        dict: Результаты скачивания {url: путь_к_файлу_или_None}
    """
    # Загрузка конфигурации

    results = {}

    # Скачивание файлов конкурентов
    for url in URLS:
        results[url] = download_xml(url, HEADERS)

    # Скачивание собственного файла
    if MY_URL:
        results[MY_URL] = download_xml(MY_URL, HEADERS)

    return results


def parse_sitemap_urls():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    urls = []
    for xml_file in xml_directory.glob("*.xml"):
        try:
            # Парсим XML файл
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Определяем пространство имен (namespace), если оно есть
            namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Ищем все теги <url> и извлекаем <loc>
            for url in root.findall(".//sitemap:url", namespace):
                loc = url.find("sitemap:loc", namespace)

                if loc is not None and loc.text:
                    urls.append(loc.text)

            # return urls

        except ET.ParseError as e:
            print(f"Ошибка парсинга XML: {e}")
            return []
        except FileNotFoundError:
            print(f"Файл {xml_file} не найден")
            return []
    logger.info(f"Найдено {len(urls)} URL-ов")


def parsin_xml():
    # Словарь соответствия имени файла и имени листа
    file_sheet_mapping = {
        "all": "my_site",
        "export_yandex_market": "insportline_out_of_stock",
        "yml_dualprice": "insportline_in_stock",
    }

    # Переменная для выбора полей, которые нужно извлечь из XML
    # Для "all" берем только offer_id и price, для остальных - все поля

    # Обрабатываем каждый XML-файл в директории
    for xml_file in xml_directory.glob("*.xml"):
        name_file = xml_file.stem

        # Пропускаем файлы, которые не указаны в маппинге
        if name_file not in file_sheet_mapping:
            continue

        sheet_name = file_sheet_mapping[name_file]

        # Парсим XML
        tree = etree.parse(xml_file)
        root = tree.getroot()
        offers = root.xpath("//offer")
        result = []

        for offer in offers[
            :1
        ]:  # Берем только первый offer для примера (в оригинале так)
            offer_id = offer.get("id")

            # Извлекаем данные из XML, используя вспомогательную функцию
            fields = {
                # "stock_quantity": extract_xml_value(offer, "stock_quantity"),
                "price": extract_xml_value(offer, "price"),
                "vendor_code": extract_xml_value(offer, "vendorCode"),
            }

            # Создаем словарь для текущего offer
            all_data = {"offer_id": offer_id}

            # Для "all" берем только offer_id и price
            if name_file == "all":
                all_data["price"] = fields["price"]
                sku = (
                    offer.xpath('param[@name="sku"]/text()')[0]
                    if offer.xpath('param[@name="sku"]')
                    else None
                )
                ean = (
                    offer.xpath('param[@name="ean"]/text()')[0]
                    if offer.xpath('param[@name="ean"]')
                    else None
                )
                all_data["sku"] = sku
                all_data["ean"] = ean
            else:
                # Для остальных файлов берем все поля
                all_data.update(fields)

            result.append(all_data)

        # Получаем лист и обновляем данные
        sheet = get_google_sheet(sheet_name)
        update_sheet_with_data(sheet, result)


def extract_xml_value(element, tag_name):
    """Извлекает значение тега из XML элемента или возвращает 'N/A', если тег не найден."""
    node = element.find(tag_name)
    return node.text if node is not None else None


if __name__ == "__main__":
    # download_all_xml_files()
    parsin_xml()
