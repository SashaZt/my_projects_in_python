# Стандартные библиотеки
import sys
import re
import csv
import shutil
import random
import threading
from threading import Lock
from pathlib import Path
import xml.etree.ElementTree as ET
import traceback

# Сторонние библиотеки
import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ваши модули
from configuration.logger_setup import logger
from get_response import Get_Response
from parsing import Parsing

# from dynamic_sqlite import DynamicSQLite
from dynamic_postgres import DynamicPostgres


# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

html_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

output_csv_file = data_directory / "output.csv"
csv_file_successful = data_directory / "identifier_successful.csv"
xlsx_result = data_directory / "result.xlsx"
file_proxy = configuration_directory / "roman.txt"


cookies = {
    "PHPSESSID": "994gpk9m3pm3v0b33t8lv5m3nv",
    "G_ENABLED_IDPS": "google",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


while True:
    max_workers = 20
    base_url = "https://www.ua-region.com.ua"
    url_sitemap = "https://www.ua-region.com.ua/sitemap.xml"
    # Запрос ввода от пользователя
    print(
        "Введите 1 для запуска полного процесса"
        "\nВведите 2 для запуска парсинга и запись в БД"
        "\nВведите 0 для закрытия программы"
    )
    user_input = int(input("Выберите действие: "))

    if user_input == 1:
        response_handler = Get_Response(
            max_workers,
            base_url,
            cookies,
            headers,
            html_files_directory,
            csv_file_successful,
            output_csv_file,
            file_proxy,
            url_sitemap,
        )
        # Запуск метода для получения всех sitemaps и обработки
        response_handler.get_all_sitemap()

        # Запуск метода скачивания html файлов
        response_handler.process_infox_file()

        # Парсинг html файлов
        processor = Parsing(html_files_directory, xlsx_result, max_workers)
        all_results = processor.parsing_html()
        processor.save_results_to_json(all_results)
        # processor.write_to_excel(all_results)
        # Создать экземпляр класса DynamicSQLite, указав имя базы данных
        # Создаем экземпляр DynamicPostgres

        db = DynamicPostgres()
        # Создаем или обновляем таблицу
        data = db.load_data_from_json()
        db.create_or_update_table("ua_region_com_ua", data)

        # Вставляем данные
        db.insert_data("ua_region_com_ua", data, num_threads=20)

        # Закрываем соединение с базой данных
        db.close()
        # db = DynamicSQLite("organizations.db")
        # # Создать или обновить структуру таблицы на основе предоставленных данных
        # db.create_or_update_table("organizations", all_results)
        # # Вставить данные в таблицу
        # db.insert_data("organizations", all_results)
        # # Закрыть соединение с базой данных
        # db.close()
    elif user_input == 2:
        processor = Parsing(html_files_directory, xlsx_result, max_workers)
        all_results = processor.parsing_html()
        processor.save_results_to_json(all_results)
        # processor.write_to_excel(all_results)
        # Создать экземпляр класса DynamicSQLite, указав имя базы данных
        db = DynamicPostgres()
        # Создаем или обновляем таблицу
        data = db.load_data_from_json()
        db.create_or_update_table("ua_region_com_ua", data)

        # Вставляем данные
        db.insert_data("ua_region_com_ua", data, num_threads=20)

        # Закрываем соединение с базой данных
        db.close()
        # db = DynamicSQLite("organizations.db")
        # # Создать или обновить структуру таблицы на основе предоставленных данных
        # db.create_or_update_table("organizations", all_results)
        # # Вставить данные в таблицу
        # db.insert_data("organizations", all_results)
        # # Закрыть соединение с базой данных
        # db.close()
    elif user_input == 0:
        print("Программа завершена.")
        break  # Выход из цикла, завершение программы
    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
