import requests
from configuration.logger_setup import logger
from bs4 import BeautifulSoup
from tqdm import tqdm
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
import requests
import random
import csv
import xml.etree.ElementTree as ET
import re
import threading
import sys


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


class Get_Response:

    def __init__(
        self,
        max_workers,
        base_url,
        cookies,
        headers,
        html_files_directory,
        csv_file_successful,
        output_csv_file,
        file_proxy,
        url_sitemap,
    ) -> None:
        # Инициализация переданных параметров как атрибутов класса
        self.max_workers = max_workers
        self.base_url = base_url
        self.cookies = cookies
        self.headers = headers
        self.html_files_directory = Path(html_files_directory)
        self.csv_file_successful = csv_file_successful
        self.output_csv_file = output_csv_file
        self.file_proxy = file_proxy
        self.url_sitemap = url_sitemap
        self.stop_event = (
            threading.Event()
        )  # Добавляем глобальное событие для остановки потоков

        # Создание экземпляра класса для работы с файлами
        self.working_files = Working_with_files(
            self.csv_file_successful, output_csv_file, self.file_proxy
        )

    def fetch_xml(self, url):
        # Загружаем список прокси-серверов из файла
        proxies = self.working_files.load_proxies()
        # Выбираем случайный прокси-сервер для запроса
        proxy = random.choice(proxies)
        proxies_dict = {"http": proxy, "https": proxy}

        # Запрос по указанному URL
        response = requests.get(
            url, proxies=proxies_dict, headers=self.headers, cookies=self.cookies
        )

        if response.status_code == 200:
            logger.info(f"Скачали sitemap: {url}")
            return response.content
        else:
            logger.error(
                f"Ошибка при скачивании файла: {response.status_code} для URL: {url}"
            )
            return None

    def get_sitemap_start(self):
        # Используем универсальный метод fetch_xml
        content = self.fetch_xml(self.url_sitemap)
        return content

    def parsing_sitemap_start(self):
        content = self.get_sitemap_start()
        if content:
            return self.parsing_sitemap(content)
        return []

    def parsing_sitemap(self, content):
        # Парсинг XML-содержимого
        root = ET.fromstring(content)

        # Определение пространства имен
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Извлечение всех тегов <loc>
        locations = root.findall(".//ns:loc", namespace)

        # Регулярное выражение для поиска нужных URL
        pattern = r"https://www\.ua-region\.com\.ua/sitemap/sitemap_\d+\.xml"

        # Генератор списков для получения всех URL, соответствующих регулярному выражению
        matching_urls = [loc.text for loc in locations if re.match(pattern, loc.text)]
        logger.info("Получили список всех sitemap")
        return matching_urls

    def get_all_sitemap(self):
        all_url_company = set()
        all_urls = self.parsing_sitemap_start()
        for url in all_urls:
            # Используем универсальный метод fetch_xml для каждого URL
            content = self.fetch_xml(url)
            if content:
                urls_company = self.parsing_all_sitemap(content)
                # Добавляем все найденные URL в множество
                all_url_company.update(urls_company)
            else:
                logger.error(f"Ошибка при обработке URL: {url}")
        logger.info(len(all_url_company))
        # Сохраняем уникальные URL в CSV-файл
        self.working_files.write_to_csv(all_url_company, self.output_csv_file)

    def parsing_all_sitemap(self, content):
        # Предполагаем, что этот метод парсит XML и возвращает список URL
        root = ET.fromstring(content)
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = root.findall(".//ns:loc", namespace)
        return [loc.text for loc in locations]

    def process_infox_file(self):
        self.working_files.remove_successful_urls()
        # Загружаем список прокси-серверов из файла
        proxies = self.working_files.load_proxies()

        # Загружаем уже обработанные URL, чтобы не обрабатывать их повторно
        successful_urls = self.working_files.get_successful_urls()

        # Загружаем список URL для обработки из CSV-файла
        urls_df = pd.read_csv(self.output_csv_file)

        # Инициализация прогресс-бара
        total_urls = len(urls_df)
        progress_bar = tqdm(
            total=total_urls,
            desc="Обработка файлов",
            bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
        )

        # Запускаем многопоточную обработку
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Создаем задачи для каждого URL в списке
            futures = [
                executor.submit(self.fetch_and_save_html, url, successful_urls, proxies)
                for url in urls_df["url"]
            ]

            # Отслеживаем выполнение задач
            for future in as_completed(futures):
                try:
                    future.result()  # Получаем результат выполнения задачи
                except Exception as e:
                    logger.error(f"Error occurred: {e}")
                    self.stop_event.set()  # Устанавливаем событие для остановки всех потоков

                finally:
                    # Обновляем прогресс-бар после каждой завершенной задачи
                    progress_bar.update(1)

        # Закрываем прогресс-бар
        progress_bar.close()
        if self.stop_event.is_set():
            logger.error("Программа остановлена из-за ошибок.")
            sys.exit(1)
        else:
            logger.info("Все запросы выполнены.")

    def fetch_and_save_html(self, url, successful_urls, proxies):
        fetch_lock = (
            threading.Lock()
        )  # Лок для синхронизации записи в общий ресурс (множество и файл)
        # Прерываем выполнение, если установлено событие остановки
        if self.stop_event.is_set():
            return
        # Проверяем, обрабатывался ли этот URL ранее
        if url in successful_urls:
            logger.info(f"| Компания уже была обработана, пропускаем. |")
            return
        identifier = url.split("/")[-1]
        try:
            # Выбираем случайный прокси-сервер для запроса
            proxy = random.choice(proxies)
            proxies_dict = {"http": proxy, "https": proxy}
            # Отправляем запрос
            response = requests.get(
                url,
                proxies=proxies_dict,
                headers=self.headers,
                cookies=self.cookies,
            )

            # Проверяем успешность запроса
            if response.status_code == 200:

                # Сохраняем HTML-файл в указанную директорию
                file_path = self.html_files_directory / f"{identifier}.html"
                file_path.write_text(response.text, encoding="utf-8")
                with fetch_lock:
                    # Добавляем идентификатор в множество успешных
                    successful_urls.add(url)

                    # Сохраняем идентификатор в CSV для отслеживания
                    self.working_files.write_to_csv(url, self.csv_file_successful)
            else:
                logger.error(
                    f"Ошибка: не удалось получить данные для {url}. Статус: {response.status_code}"
                )
                self.stop_event.set()  # Устанавливаем событие остановки

        except Exception as e:
            logger.error(f"Произошла ошибка при обработке {url}: {e}")
            self.stop_event.set()  # Устанавливаем событие остановки


class Working_with_files:

    def __init__(self, csv_file_successful, output_csv_file, file_proxy) -> None:
        # Сохраняем пути к файлам как атрибуты класса
        self.csv_file_successful = csv_file_successful
        self.output_csv_file = output_csv_file
        self.file_proxy = file_proxy
        self.header_written = False  # Флаг для отслеживания записи заголовка
        self.write_lock = threading.Lock()  # Создаем блокировку для записи в файл

    def load_proxies(self):
        # Загружаем список прокси-серверов из файла
        with open(self.file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        return proxies

    def write_to_csv(self, data, filename):
        # Проверяем, существует ли файл
        file_path = Path(filename)

        with self.write_lock:  # Используем блокировку для защиты кода записи в файл
            # Проверка на необходимость добавления заголовка
            if not self.header_written:
                if not file_path.exists() or file_path.stat().st_size == 0:
                    with open(filename, "a", encoding="utf-8") as f:
                        f.write("url\n")
                self.header_written = (
                    True  # Устанавливаем флаг после добавления заголовка
                )

            # Проверяем, является ли `data` итерируемым (множеством, списком) или одиночным значением
            if isinstance(data, (set, list, tuple)):
                urls_to_write = data
            else:
                urls_to_write = [data]  # Преобразуем одиночный URL в список

            # Записываем каждый URL в новую строку CSV-файла
            with open(filename, "a", encoding="utf-8") as f:
                for url in urls_to_write:
                    f.write(f"{url}\n")

    def get_successful_urls(self):
        # Загружаем уже обработанные идентификаторы из CSV-файла
        if not Path(self.csv_file_successful).exists():
            return set()

        with open(self.csv_file_successful, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            successful_urls = {
                row[0] for row in reader if row
            }  # Собираем идентификаторы в множество
        return successful_urls

    def remove_successful_urls(self):
        # Проверяем, существует ли файл с успешными URL и не является ли он пустым
        if (
            not self.csv_file_successful.exists()
            or self.csv_file_successful.stat().st_size == 0
        ):
            logger.info(
                "Файл urls_successful.csv не существует или пуст, ничего не делаем."
            )
            return

        # Загружаем данные из обоих CSV файлов
        try:
            # Читаем output_csv_file с заголовком
            df_products = pd.read_csv(self.output_csv_file)

            # Читаем csv_file_successful с заголовком
            df_successful = pd.read_csv(self.csv_file_successful)
        except FileNotFoundError as e:
            logger.error(f"Ошибка: {e}")
            return
        except pd.errors.EmptyDataError as e:
            logger.error(f"Ошибка при чтении файла: {e}")
            return

        # Проверка на наличие столбца 'url' в df_products
        if "url" not in df_products.columns or "url" not in df_successful.columns:
            logger.info("Один из файлов не содержит колонку 'url'.")
            return

        # Удаляем успешные URL из списка продуктов
        initial_count = len(df_products)
        df_products = df_products[~df_products["url"].isin(df_successful["url"])]
        final_count = len(df_products)

        # Если были удалены какие-то записи
        if initial_count != final_count:
            # Перезаписываем файл output_csv_file
            df_products.to_csv(self.output_csv_file, index=False)
            logger.info(
                f"Удалено {initial_count - final_count} записей из {self.output_csv_file.name}."
            )

            # Очищаем файл csv_file_successful
            open(self.csv_file_successful, "w").close()
            logger.info(f"Файл {self.csv_file_successful.name} очищен.")
        else:
            logger.info("Не было найдено совпадающих URL для удаления.")


max_workers = 50
base_url = "https://www.ua-region.com.ua"
url_sitemap = "https://www.ua-region.com.ua/sitemap.xml"
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
# response_handler.get_all_sitemap()

response_handler.process_infox_file()
