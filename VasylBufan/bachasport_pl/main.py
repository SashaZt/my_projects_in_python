import argparse
import json
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional

import gspread
from config.logger import logger
from google.oauth2.service_account import Credentials
from src.auth import get_session
from src.category import get_category_urls
from src.pagination import get_product_urls_from_category
from src.product import get_product_details
from src.site import (
    crawl_bachasport,
    merge_product_data_files,
    parse_html_files_to_json,
)
from src.utils import random_pause
from src.xml_handler import (
    extract_simplified_product_data,
    process_all_xml_files,
    process_all_xml_files_simplified,
)

current_directory = Path.cwd()
temp_directory = current_directory / "temp"
xml_directory = temp_directory / "xml"
results_directory = temp_directory / "results"
config_directory = current_directory / "config"

temp_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
config_file_path = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"


def load_json_data(file_path):
    """Загрузка данных из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из {file_path}: {e}")
        return None


config = load_json_data(config_file_path)
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


sheet = get_google_sheet(SHEET)


def main():
    """
    Основная функция для запуска скрапинга.
    """
    logger.info("Запуск скрапера...")
    if os.path.exists(temp_directory):
        shutil.rmtree(temp_directory)
    temp_directory.mkdir(parents=True, exist_ok=True)
    xml_directory.mkdir(parents=True, exist_ok=True)
    try:
        # Получаем авторизованную сессию
        session = get_session()
        if not session:
            logger.critical("Не удалось получить сессию. Завершение программы.")
            return

        # Получаем ссылки категорий со стартовой страницы
        category_urls = get_category_urls(session)
        if not category_urls:
            logger.error("Не удалось получить ссылки категорий. Завершение программы.")
            return

        logger.info(f"Найдено {len(category_urls)} категорий")
        # Собираем URL продуктов из всех категорий
        all_product_urls = []
        for i, category_url in enumerate(category_urls):
            logger.info(
                f"Обработка категории {i+1}/{len(category_urls)}: {category_url}"
            )

            # Получаем URL продуктов из категории, включая пагинацию
            product_urls = get_product_urls_from_category(session, category_url)
            all_product_urls.extend(product_urls)

            # Делаем паузу между обработкой разных категорий
            if i < len(category_urls) - 1:  # Не делаем паузу после последней категории
                random_pause(3, 8)

        # Удаляем дубликаты URL продуктов
        unique_product_urls = list(set(all_product_urls))
        logger.info(f"Найдено {len(unique_product_urls)} уникальных продуктов")

        # Скачиваем XML каждого продукта
        success_count = 0
        products_data = []
        for i, product_url in enumerate(unique_product_urls):
            logger.info(
                f"Обработка продукта {i+1}/{len(unique_product_urls)}: {product_url}"
            )

            # Получаем детали продукта и скачиваем XML
            product_id, xml_path, availability = get_product_details(
                session, product_url
            )
            product_info = {
                "availability": availability,
            }
            if product_id and xml_path:

                # Добавляем информацию о доступности, если она есть
                if availability:
                    product_info["availability"] = availability

                # Извлекаем данные из XML сразу после скачивания
                xml_file_path = Path(xml_path)
                if xml_file_path.exists():
                    xml_data = extract_simplified_product_data(xml_file_path)
                    if xml_data:
                        # Дополняем информацию о продукте данными из XML
                        product_info.update(xml_data)

                products_data.append(product_info)
                success_count += 1
                logger.info(f"Успешно обработан продукт {product_id}")
            else:
                logger.warning(f"Не удалось скачать XML для продукта {product_url}")

            # Делаем паузу между запросами к продуктам
            if (
                i < len(unique_product_urls) - 1
            ):  # Не делаем паузу после последнего продукта
                random_pause(1, 4)

        file_name = temp_directory / "complete_products_data.json"
        with open(file_name, "w", encoding="utf-8") as json_file:
            json.dump(products_data, json_file, ensure_ascii=False, indent=4)

        crawl_bachasport()
        parse_html_files_to_json()
        merge_product_data_files()

        result_file = temp_directory / "result.json"
        with open(result_file, "r", encoding="utf-8") as f:
            complete_data = json.load(f)
        update_sheet_with_data(sheet, complete_data)

    except KeyboardInterrupt:
        logger.info("Скрапинг прерван пользователем.")
    except Exception as e:
        logger.critical(f"Критическая ошибка в основной функции: {e}")


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
    main()
