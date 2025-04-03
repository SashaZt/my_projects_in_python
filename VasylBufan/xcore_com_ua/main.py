import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import demjson3
import gspread
import pandas as pd
import requests
from bs4 import BeautifulSoup
from config.logger import logger
from google.oauth2.service_account import Credentials

current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = current_directory / "xml"
log_directory = current_directory / "log"
config_directory = current_directory / "config"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)

data_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"
urls_xml_file_path = data_directory / "urls_xml.csv"
urls_product_file_path = data_directory / "urls.csv"
output_json_file = data_directory / "output.json"
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
URL_XML = config.get("url_xml")
COOKIES = config.get("cookies", {})
HEADERS = config.get("headers", {})
FILENAME_XML = urlparse(URL_XML).path.split("/")[-1]
XML_FILE_PATH = xml_directory / f"{FILENAME_XML}"
SPREADSHEET = config["google"]["spreadsheet"]
SHEET_ALL = config["google"]["sheet_all"]
SHEET_01 = config["google"]["sheet_01"]


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


def download_with_curl(url, xml_file_path):
    """
    Скачивает файл по URL используя системную команду curl

    Returns:
        str or None: Путь к скачанному файлу или None в случае ошибки
    """
    try:

        # Создаем директорию, если она не существует

        logger.info(f"Начинаю скачивание файла с {url}")

        # Формируем команду curl
        command = [
            "curl",
            "-o",
            xml_file_path,  # Выходной файл
            "-L",  # Следовать редиректам
            "-A",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",  # User-Agent
            "--max-redirs",
            "10",  # Максимальное количество редиректов
            "--connect-timeout",
            "30",  # Тайм-аут соединения
            url,
        ]

        # Выполняем команду
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            logger.info(f"Файл успешно сохранен в: {xml_file_path}")
            return xml_file_path
        else:
            logger.error(f"Ошибка при скачивании файла: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return None


def download_all_xml():
    """
    Скачивает XML файл(ы) по указанному URL или списку URL.

    Args:
        urls (str или list): URL или список URL для скачивания XML файлов
        cookies (dict): Cookies для HTTP запроса
        headers (dict): Заголовки для HTTP запроса

    Returns:
        list или Path или None: Список путей к сохраненным файлам, путь к файлу или None в случае ошибки
    """
    # Чтение CSV-файла с URL
    urls_df = pd.read_csv(urls_xml_file_path, encoding="utf-8")
    urls = urls_df["url"].tolist()
    for url in urls:
        try:
            # Получаем имя файла из URL
            file_name = urlparse(url).path.split("/")[-1]
            xml_file_path = xml_directory / file_name

            download_with_curl(url, xml_file_path)
        except Exception as e:
            logger.error(f"Ошибка при обработке URL {url}: {e}")
            # Продолжаем со следующим URL


def parse_sitemap_urls():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    urls = []
    for xml_file in xml_directory.glob("jetsitemap-products-page-1*.xml"):
        try:
            # Парсим XML файл
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Ищем все элементы <url> в пространстве имён
            for url_elem in root.findall(
                ".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"
            ):
                loc = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if loc is not None:
                    urls.append(loc.text)

        except ET.ParseError as e:
            logger.error(f"Ошибка парсинга XML {xml_file}: {e}")
            return []
        except FileNotFoundError:
            logger.error(f"Файл {xml_file} не найден")
            return []

    logger.info(f"Найдено {len(urls)} URL-ов")

    # Сохранение в CSV
    if urls:  # Сохраняем только если есть URL
        url_data = pd.DataFrame(urls, columns=["url"])
        url_data.to_csv(urls_product_file_path, index=False)
        logger.info(f"URL сохранены в {urls_product_file_path}")


def parsin_xml(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        xml_content = file.read()

    # Парсим XML
    root = ET.fromstring(xml_content)

    # Находим все элементы <loc>
    product_sitemaps = []
    for sitemap in root.findall(
        ".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"
    ):
        loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        if loc is not None and "jetsitemap-products-page-" in loc.text:
            product_sitemaps.append(loc.text)
    url_data = pd.DataFrame(product_sitemaps, columns=["url"])
    url_data.to_csv(urls_xml_file_path, index=False)
    logger.info(f"Сохранил {urls_xml_file_path}")


def fetch(url):
    """
    Загружает содержимое URL с повторными попытками в случае ошибки.

    Args:
        url (str): URL для загрузки

    Returns:
        str or None: Текст ответа или None в случае неудачи
    """
    max_attempts = 10
    delay_seconds = 5

    for attempt in range(max_attempts):
        try:
            response = requests.get(
                url, cookies=COOKIES, headers=HEADERS, timeout=100, stream=True
            )

            # Проверка статуса ответа
            if response.status_code == 200:
                # Принудительно устанавливаем кодировку UTF-8
                response.encoding = "utf-8"
                return response.text
            else:
                logger.warning(
                    f"Попытка {attempt + 1}/{max_attempts}: Статус {response.status_code} для {url}. Ждём {delay_seconds} секунд."
                )
                if attempt < max_attempts - 1:  # Не ждём после последней попытки
                    time.sleep(delay_seconds)

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Попытка {attempt + 1}/{max_attempts}: Ошибка при загрузке {url}: {str(e)}"
            )
            if attempt < max_attempts - 1:
                time.sleep(delay_seconds)
            else:
                logger.error(f"Все {max_attempts} попыток неудачны для {url}")
                return None

    logger.error(f"Все {max_attempts} попыток неудачны для {url} (статус не 200)")
    return None


def get_html(url, html_file):
    src = fetch(url)

    if src is None:
        return url, html_file, False

    with open(html_file, "w", encoding="utf-8") as file:
        file.write(src)

    logger.info(f"Успешно загружен и сохранен: {html_file}")
    return url, html_file, True


def main_th():
    if not os.path.exists(html_directory):
        html_directory.mkdir(parents=True, exist_ok=True)
    urls = []
    with open(urls_product_file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            urls.append(row["url"])

    with ThreadPoolExecutor(max_workers=10) as executor:
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


def extract_product_data(product_json):
    """
    Извлекает данные продукта из JSON структуры

    Args:
        product_json (dict): JSON структура продукта

    Returns:
        dict: Извлеченные данные продукта
    """
    try:
        data_json_all = {}
        data_json_01 = {}
        product_name = product_json.get("name")
        model = product_json.get("model")
        sku = product_json.get("sku")

        # Извлекаем данные из offers
        offers = product_json.get("offers", {})
        offer_price = None
        if "price" in offers:
            offer_price = offers.get("price")
        elif "lowPrice" in offers:
            offer_price = offers.get("lowPrice")
        offer_price = str(offer_price).replace(".", ",")
        availability = offers.get("availability")
        schema_terms = (
            r"(InStock|PreOrder|OutOfStock|Discontinued)"  # Шаблон для поиска
        )
        all_availability = {
            "PreOrder": "Попереднє замовлення",
            "InStock": "В наявності",
            "OutOfStock": "Немає в наявності",
            "Discontinued": "Припинено",
        }

        matches = re.findall(schema_terms, availability or "")  # Проверяем на None
        result_availability = None
        if matches:
            last_term = matches[-1]
            result_availability = all_availability[last_term]
        if model.endswith("~01"):
            data_json_01 = {
                "Назва": product_name,
                "Код товару": model,
                "Артику": sku,
                "Ціна": offer_price,
                "Наявність": result_availability,
            }
        else:
            data_json_all = {
                "Назва": product_name,
                "Код товару": model,
                "Артику": sku,
                "Ціна": offer_price,
                "Наявність": result_availability,
            }

        return data_json_all, data_json_01
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных продукта: {e}")
        return None


def pars_htmls():
    logger.info("Собираем данные со страниц html")
    list_all = []
    list_01 = []
    all_product = []
    html_count = len(list(html_directory.glob("*.html")))
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        soup = BeautifulSoup(content, "lxml")
        # Находим все скрипты с типом application/ld+json
        scripts = soup.find_all("script", type="application/ld+json")

        if not scripts:
            logger.warning(
                f"В файле {html_file.name} не найдено скриптов с типом application/ld+json"
            )
            continue

        # Перебираем все скрипты JSON-LD
        for script in scripts:
            try:
                # Получаем текст скрипта и проверяем его наличие
                script_text = script.string
                if not script_text or not script_text.strip():
                    continue

                # Проверим, что это скрипт JSON-LD
                if "application/ld+json" not in script.get("type", ""):
                    continue

                # Удаляем неразрывные пробелы и контрольные символы
                cleaned_text = script_text.strip()

                # Регулярное выражение для удаления управляющих символов
                cleaned_text = re.sub(r"[\x00-\x1F\x7F]", "", cleaned_text)

                # Убедимся, что JSON правильно сбалансирован
                opening_braces = cleaned_text.count("{")
                closing_braces = cleaned_text.count("}")

                if opening_braces > closing_braces:
                    # Добавляем недостающие закрывающие скобки
                    cleaned_text += "}" * (opening_braces - closing_braces)
                    logger.info(
                        f"Добавлены недостающие закрывающие скобки: {opening_braces - closing_braces}"
                    )

                try:
                    json_data = json.loads(cleaned_text)
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка парсинга JSON: {e}")

                    # Дополнительные исправления
                    # 1. Выравнивание отступов для ключей gtin и sku
                    cleaned_text = re.sub(r'(\s+)"(gtin|sku)"', r'"$2"', cleaned_text)

                    # 2. Проверка наличия закрывающей скобки в конце
                    if not cleaned_text.rstrip().endswith("}"):
                        cleaned_text = cleaned_text.rstrip() + "}"

                    try:
                        json_data = json.loads(cleaned_text)
                        logger.info("JSON успешно исправлен и распарсен")
                        # Извлекаем данные основного продукта

                    except json.JSONDecodeError as e2:
                        # Альтернативный подход - использовать более гибкий парсер
                        try:

                            json_data = demjson3.decode(cleaned_text)
                            logger.info("JSON успешно распарсен с помощью demjson3")
                        except Exception:
                            logger.error(f"Не удалось исправить JSON: {e2}")
                            continue

                if json_data.get("@type") == "BreadcrumbList":
                    continue
                if json_data.get("@type") == "Product":
                    sklad_all, sklad_01 = extract_product_data(json_data)
                    if sklad_all:
                        list_all.append(sklad_all)
                        all_product.append(sklad_all)
                        html_count -= 1
                        print(f"Осталось обработать: {html_count} файлов", end="\r")
                    if sklad_01:
                        list_01.append(sklad_01)
                        all_product.append(sklad_01)
                        html_count -= 1
                        print(f"Осталось обработать: {html_count} файлов", end="\r")

            except Exception as e:
                logger.error(f"Непредвиденная ошибка при обработке скрипта: {str(e)}")

    with open(output_json_file, "w", encoding="utf-8") as json_file:
        json.dump(all_product, json_file, ensure_ascii=False, indent=4)
    # Получение листа Google Sheets
    if list_all:
        sheet = get_google_sheet(SHEET_ALL)
        update_sheet_with_data(sheet, list_all)
    if list_01:
        sheet = get_google_sheet(SHEET_01)
        update_sheet_with_data(sheet, list_01)


## Код для увеличение количества строк
# def ensure_row_limit(sheet, required_rows=10000):
#     """Увеличивает количество строк в листе Google Sheets, если их меньше требуемого количества."""
#     current_rows = len(sheet.get_all_values())
#     if current_rows < required_rows:
#         sheet.add_rows(required_rows - current_rows)


# ensure_row_limit(sheet, 1000)

if __name__ == "__main__":
    download_with_curl(URL_XML, XML_FILE_PATH)
    parsin_xml(XML_FILE_PATH)
    download_all_xml()
    parse_sitemap_urls()
    main_th()
    pars_htmls()
