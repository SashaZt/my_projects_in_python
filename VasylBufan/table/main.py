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


def update_sheet_with_data(sheet, data, total_rows=20000):
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
    # Словарь для хранения данных по sku
    data_dict = {}
    # Дополнительный словарь для хранения данных по ean для быстрого поиска
    ean_dict = {}
    # Словарь для сопоставления SKU без префикса INS
    normalized_sku_dict = {}

    # Для хранения данных в разных категориях
    matched_data = []  # Данные, которые были сопоставлены
    unmatched_data = []  # Данные, которые не были сопоставлены

    # Сначала обрабатываем файл "all", чтобы собрать sku и ean
    for xml_file in xml_directory.glob("*.xml"):
        name_file = xml_file.stem

        if name_file == "all":
            tree = etree.parse(xml_file)
            root = tree.getroot()
            offers = root.xpath("//offer")

            for offer in offers:
                price_my_site = extract_xml_value(offer, "price")
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

                if sku:  # Используем sku как ключ
                    data_dict[sku] = {
                        "Мой сайт sku": sku,
                        "Мой сайт ean": ean,
                        "Мой сайт цена": price_my_site,
                        "insportline": None,
                        "insportline цена": None,
                        "matched": False,  # Флаг для отслеживания сопоставленных записей
                    }

                    # Если есть EAN, создаем ссылку на запись в data_dict
                    if ean:
                        ean_dict[ean] = sku

                    # Создаем нормализованную версию SKU (без префикса INS)
                    normalized_sku = normalize_sku(sku)
                    normalized_sku_dict[normalized_sku] = sku

    # Теперь обрабатываем остальные файлы для получения insportline (vendorCode)
    for xml_file in xml_directory.glob("*.xml"):
        name_file = xml_file.stem

        if name_file in ["export_yandex_market", "yml_dualprice"]:
            tree = etree.parse(xml_file)
            root = tree.getroot()
            offers = root.xpath("//offer")

            for offer in offers:
                vendor_code = extract_xml_value(offer, "vendorCode")
                insportline_price = extract_xml_value(offer, "price")

                if not vendor_code:
                    continue

                match_found = False

                # Пытаемся найти соответствующую запись по sku
                if vendor_code in data_dict:
                    # Сопоставление по точному совпадению SKU
                    data_dict[vendor_code]["insportline vendor_code"] = vendor_code
                    data_dict[vendor_code]["insportline цена"] = insportline_price
                    data_dict[vendor_code]["matched"] = True
                    match_found = True
                else:
                    # Нормализуем vendor_code для сравнения
                    normalized_vendor = normalize_sku(vendor_code)

                    # Проверяем соответствие по нормализованному SKU
                    if normalized_vendor in normalized_sku_dict:
                        original_sku = normalized_sku_dict[normalized_vendor]
                        data_dict[original_sku]["insportline vendor_code"] = vendor_code
                        data_dict[original_sku]["insportline цена"] = insportline_price
                        data_dict[original_sku]["matched"] = True
                        match_found = True
                    else:
                        # Попробуем сопоставить по EAN
                        ean_value = extract_xml_value(
                            offer, "barcode"
                        ) or extract_xml_value(offer, "ean")

                        if ean_value and ean_value in ean_dict:
                            # Нашли соответствие по EAN
                            matching_sku = ean_dict[ean_value]
                            data_dict[matching_sku][
                                "insportline vendor_code"
                            ] = vendor_code
                            data_dict[matching_sku][
                                "insportline цена"
                            ] = insportline_price
                            data_dict[matching_sku]["matched"] = True
                            match_found = True

                if not match_found:
                    # Если нет соответствия ни по SKU, ни по EAN, добавляем новую запись
                    new_key = f"insportline_{vendor_code}"
                    data_dict[new_key] = {
                        "Мой сайт sku": None,
                        "Мой сайт ean": None,
                        "Мой сайт цена": None,
                        "insportline vendor_code": vendor_code,
                        "insportline цена": insportline_price,
                        "matched": False,  # Это несопоставленная запись
                    }

    # Разделяем данные на сопоставленные и несопоставленные
    for key, value in data_dict.items():
        # Удаляем служебное поле matched, которое не нужно передавать в result
        matched = value.pop("matched", False)

        if matched:
            matched_data.append(value)
        else:
            unmatched_data.append(value)

    # Выводим для отладки количество сопоставленных и несопоставленных записей
    print(f"Сопоставлено записей: {len(matched_data)}")
    print(f"Не сопоставлено записей: {len(unmatched_data)}")

    # Соединяем сначала сопоставленные, затем несопоставленные записи
    result = matched_data + unmatched_data

    # Для примера выведем первые несколько сопоставленных записей
    print("\nПримеры сопоставленных записей:")
    for i, item in enumerate(matched_data[:5]):  # Первые 5 записей для примера
        print(
            f"{i+1}. SKU: {item['Мой сайт sku']}, EAN: {item['Мой сайт ean']}, "
            + f"Мой сайт цена: {item['Мой сайт цена']}, "
            + f"Insportline: {item['insportline']}, Insportline цена: {item['insportline цена']}"
        )

    # Получаем лист и обновляем данные
    sheet_name = "Data"
    sheet = get_google_sheet(sheet_name)
    update_sheet_with_data(sheet, result)

    return result  # Возвращаем результат для дальнейшего использования
    # # Преобразуем словарь в список для записи
    # result = list(data_dict.values())

    # # Получаем лист и обновляем данные
    # sheet_name = "Data"
    # sheet = get_google_sheet(sheet_name)
    # update_sheet_with_data(sheet, result)


def normalize_sku(sku):
    """
    Нормализует SKU, удаляя префикс 'INS' если он есть.
    Например: 'INS9410-3' -> '9410-3'
    """
    if sku and isinstance(sku, str):
        if sku.startswith("INS"):
            return sku[3:]  # Удаляем первые 3 символа (INS)
    return sku


def extract_xml_value(element, tag_name):
    """Извлекает значение тега из XML элемента или возвращает 'N/A', если тег не найден."""
    node = element.find(tag_name)
    return node.text if node is not None else None


if __name__ == "__main__":
    # download_all_xml_files()
    parsin_xml()
