import asyncio
import csv
import json
import os
import random
import re
import shutil
import time
from pathlib import Path
from typing import Dict, List, Tuple

import aiofiles
import gspread
import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.config_utils import (
    initialize_directories,
    load_environment_variables,
)
from configuration.logger_setup import logger
from oauth2client.service_account import ServiceAccountCredentials
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.axis import ChartLines
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

# Инициализация директорий
base_directory = Path.cwd()
directories = initialize_directories(base_directory)

# Загрузка переменных окружения
env_file = directories["config_dir"] / ".env"
env_vars = load_environment_variables(env_file)

# Настройка временных параметров и лимитов
time_a = int(env_vars["TIME_A"])
time_b = int(env_vars["TIME_B"])
SPREADSHEET = str(env_vars["SPREADSHEET"])
SHEET = str(env_vars["SHEET"])

# количество строк, которых можно записать за один проход
BATCH_SIZE = int(env_vars["BATCH_SIZE"])

# Пауза между запросами на сайт
PAUSE_DURATION = int(env_vars["PAUSE_DURATION"])

EMAIL = str(env_vars["EMAIL"])
PASSWORD = str(env_vars["PASSWORD"])


def read_cities_from_csv(input_csv_file: str) -> List[str]:
    """Читает список URL из столбца 'url' CSV-файла.

    Args:
        input_csv_file (str): Путь к входному CSV-файлу.

    Returns:
        List[str]: Список URL-адресов из столбца 'url'.

    Raises:
        ValueError: Если файл не содержит столбца 'url'.
        FileNotFoundError: Если файл не найден.
    """
    try:
        with open(input_csv_file, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if "url" not in reader.fieldnames:
                raise ValueError("Входной файл не содержит столбца 'url'.")

            urls = [
                row["url"] for row in reader if row["url"]
            ]  # Считываем только непустые значения
            return urls

    except FileNotFoundError:
        raise FileNotFoundError(f"Файл {input_csv_file} не найден.")

    except ValueError as e:
        raise e


def read_urls_from_txt(input_txt_file: str) -> List[str]:
    """Читает список URL из текстового файла.

    Args:
        input_txt_file (str): Путь к входному текстовому файлу.

    Returns:
        List[str]: Список URL-адресов.

    Raises:
        FileNotFoundError: Если файл не найден.
        IOError: Если файл пустой или произошла ошибка при чтении.
    """
    try:
        with open(input_txt_file, "r", encoding="utf-8") as file:
            urls = [
                line.strip() for line in file if line.strip()
            ]  # Убираем пустые строки и лишние пробелы
            return urls

    except FileNotFoundError:
        raise FileNotFoundError(f"Файл {input_txt_file} не найден.")

    except IOError as e:
        raise IOError(f"Ошибка при чтении файла {input_txt_file}: {e}")


# Получение куки
def get_cookies(config_file: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Извлекает заголовки и куки из строки curl, хранящейся в указанном файле.

    Args:
        config_file (str): Путь к файлу, содержащему строку curl.

    Returns:
        Tuple[Dict[str, str], Dict[str, str]]:
            - headers (Dict[str, str]): Словарь заголовков.
            - cookies (Dict[str, str]): Словарь куки.

    Raises:
        FileNotFoundError: Если файл не найден.
        ValueError: Если файл не содержит корректную строку curl.
    """
    # Чтение строки curl из файла
    with open(config_file, "r", encoding="utf-8") as f:
        curl_text = f.read()

    # Инициализация словарей для заголовков и кук
    headers = {}
    cookies = {}

    # Извлечение всех заголовков из параметров `-H`
    header_matches = re.findall(r"-H '([^:]+):\s?([^']+)'", curl_text)
    for header, value in header_matches:
        if header.lower() == "cookie":
            # Обработка куки отдельно, разделяя их по `;`
            cookies = {
                k.strip(): v
                for pair in value.split("; ")
                if "=" in pair
                for k, v in [pair.split("=", 1)]
            }
        else:
            headers[header] = value

    return headers, cookies


def get_google_sheet():
    """Подключается к Google Sheets и возвращает указанный лист.

    Настраивает доступ, авторизуется и открывает таблицу по ключу.
    """
    # Настройка доступа и авторизация
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]

    # Укажи путь к файлу с учетными данными для Google API
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        directories["credentials"], scope
    )
    client = gspread.authorize(creds)

    # Открыть таблицу по ключу и вернуть указанный лист
    spreadsheet = client.open_by_key(SPREADSHEET)
    return spreadsheet.worksheet(SHEET)


# Получение листа Google Sheets
sheet = get_google_sheet()


def get_html():
    """Авторизуется на сайте и скачивает HTML-страницы для каждого сайта из списка, учитывая лимит и текущий прогресс.

    Функция использует сессию для авторизации на сайте и загружает HTML-страницы выбранных сайтов,
    записывая их в указанные файлы, если они еще не были загружены.

    Примечания:
        - Список сайтов загружается из текстового файла.
        - HTML-страницы сохраняются в указанной директории.
    """
    sites = read_urls_from_txt(directories["txt_file"])
    # Создаем сессию
    session = requests.Session()
    # Делаем POST запрос для авторизации
    login_url = "https://polanik.shop/en_GB/login"
    login_payload = {"mail": EMAIL, "pass": PASSWORD}
    login_headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://polanik.shop",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "referer": "https://polanik.shop/en_GB/login",
    }
    # Авторизуемся на сайте и сохраняем куки в сессии
    response = session.post(login_url, data=login_payload, headers=login_headers)

    # Обработка выбранных сайтов
    for url in sites:
        protected_headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "referer": "https://polanik.shop/en_GB/",
        }
        url_id = url.rsplit("/", maxsplit=1)[-1]
        product_id = url.rsplit("/", maxsplit=2)[-2]

        file_page_file = directories["html_dir"] / f"{product_id}_{url_id}.html"
        if file_page_file.exists():
            continue
        response = session.get(url, headers=protected_headers)
        if response.status_code == 200:
            # Сохранение HTML-страницы целиком
            with open(file_page_file, "w", encoding="utf-8") as file:
                file.write(response.text)
            pause = random_pause(time_a, time_b)


def random_pause(min_seconds: int = 30, max_seconds: int = 60) -> int:
    """Выполняет случайную паузу в заданном диапазоне.

    Args:
        min_seconds (int): Минимальная длительность паузы (целое число).
        max_seconds (int): Максимальная длительность паузы (целое число).

    Returns:
        int: Фактическая длительность паузы.
    """
    if min_seconds > max_seconds:
        raise ValueError("min_seconds не может быть больше max_seconds")

    pause_duration = random.randint(
        min_seconds, max_seconds
    )  # Используем randint для целых чисел
    logger.info(f"Пауза {pause_duration} секунд.")
    time.sleep(pause_duration)
    return pause_duration


def get_parsing():
    all_data = []
    for html_file in directories["html_dir"].glob("*.html"):
        with open(html_file, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        name_product = None
        availability_product = None
        price_product = None
        sku_product = None
        try:
            name_product = soup.find("h1", attrs={"itemprop": "name"}).text
        except:
            continue
            name_product = None
        try:

            price_product = (
                soup.find("em", attrs={"class": "main-price"})
                .text.replace("€", "")
                .replace(".", ",")
            )
        except:
            price_product = 0
        try:
            availability_product = soup.select_one(
                "div.product_cell.cell_2 > div > div > span.second"
            ).text
            if availability_product == "out of stock":
                availability_product = "Немає в наявності"
            else:
                availability_product = "В наявноті"
        except:
            availability_product = None
        try:

            sku_product = soup.select_one(
                "div.productdetails-more-details.clearfix > div > div.row.code > span"
            ).text
            # sku_product = f"INT-{sku_product}"
        except:
            sku_product = None
        result = {
            "Назва": name_product,
            "Артикул": sku_product,
            "Прайс": price_product,
            "Наявність": availability_product,
        }
        all_data.append(result)
    logger.info("Загружаем данные в Google Таблицу")
    update_sheet_with_data(sheet, all_data)
    # data_df = pd.DataFrame(all_data)

    # # Сохраняем данные в новый Excel файл
    # data_df.to_excel(directories["results_report"], index=False)


# Увеличение количества строк на листе до 1500, если необходимо
def ensure_row_limit(sheet, required_rows=1500):
    """Увеличивает количество строк в листе Google Sheets, если оно меньше требуемого.

    Args:
        sheet: Объект листа Google Sheets, в котором будет проверяться количество строк.
        required_rows (int): Минимальное количество строк, которое должно быть в листе.
    """
    current_rows = len(sheet.get_all_values())
    if current_rows < required_rows:
        sheet.add_rows(required_rows - current_rows)


# Увеличиваем количество строк до 1500, если необходимо
ensure_row_limit(sheet, 1500)


# Функция для записи заголовков в первую строку листа Google Sheets
def write_headers(sheet, headers):
    """Записывает заголовки в первую строку листа Google Sheets.

    Args:
        sheet: Объект листа Google Sheets, в который будет производиться запись.
        headers (list of str): Список заголовков для записи в первую строку.
    """
    cell_list = sheet.range(1, 1, 1, len(headers))
    for i, cell in enumerate(cell_list):
        cell.value = headers[i]
    sheet.update_cells(cell_list)


# Функция для записи данных в указанные столбцы листа Google Sheets с использованием пакетного обновления
def update_sheet_with_data(sheet, data, batch_size=10, pause_duration=5):
    """Записывает данные в указанные столбцы листа Google Sheets с использованием пакетного обновления.

    Для каждой записи в `data`, функция находит соответствующую строку по домену,
    и обновляет определенные столбцы на основании ключей словаря `entry`.
    Обновления выполняются пакетно (`batch update`) для повышения эффективности.

    Args:
        sheet: Объект листа Google Sheets, в который будет производиться запись.
        data (list of dict): Список словарей, содержащих данные для обновления.

    Примечания:
        - Пакетное обновление (`batch_update`) выполняется каждые `batch_size` записей или по завершению обработки всех данных.
        - Пауза (`pause_duration`) добавляется после каждых `batch_size` записей для предотвращения превышения квоты запросов.
    """
    headers = list(data[0].keys())
    write_headers(sheet, headers)  # Записываем заголовки один раз

    updates = []
    for i, entry in enumerate(data):
        for key, value in entry.items():
            if key in headers:  # Используем сохраненные заголовки
                col_index = (
                    headers.index(key) + 1
                )  # Находим индекс колонки по заголовку
                row_index = (
                    i + 2
                )  # Начинаем со 2 строки, так как первая строка - заголовок
                cell_range = gspread.utils.rowcol_to_a1(row_index, col_index)
                updates.append({"range": cell_range, "values": [[value]]})

        # Добавляем паузу после каждых batch_size записей
        if (i + 1) % BATCH_SIZE == 0 or i == len(data) - 1:
            if updates:
                sheet.batch_update(
                    [
                        {"range": update["range"], "values": update["values"]}
                        for update in updates
                    ]
                )
                updates = []
            logger.info(
                f"Пауза на {PAUSE_DURATION} секунд для предотвращения превышения квоты..."
            )
            time.sleep(PAUSE_DURATION)
    shutil.rmtree(directories["html_dir"])


if __name__ == "__main__":
    get_html()
    get_parsing()
