import requests
import requests
from configuration.logger_setup import logger
import random
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import xml.etree.ElementTree as ET
import requests
from configuration.logger_setup import logger
from bs4 import BeautifulSoup
from tqdm import tqdm
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
import random
import csv
import xml.etree.ElementTree as ET
import re
import threading
import sys
from dotenv import load_dotenv
import os
import asyncio
from databases import Database


current_directory = Path.cwd()
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"
img_directory = current_directory / "img"
html_files_directory = current_directory / "html_files"


data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
img_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(parents=True, exist_ok=True)

output_csv_file = data_directory / "output.csv"
file_proxy = configuration_directory / "proxy.txt"
csv_file_successful = data_directory / "identifier_successful.csv"
xlsx_result = data_directory / "result.xlsx"
# Создаем путь к файлу .env
env_file_path = configuration_directory / ".env"

# Загружаем переменные окружения из файла .env
load_dotenv(env_file_path)

cookies = {
    "device-referrer": "https://www.google.com/",
    "advanced-frontend": "gsb71blijdi0183vuoh8b4i5ba",
    "_csrf-frontend": "55d068b1627cf15ff7363e11b6fbc4b27a348f3bfc77643eea3ac4671d5a3fd4a%3A2%3A%7Bi%3A0%3Bs%3A14%3A%22_csrf-frontend%22%3Bi%3A1%3Bs%3A32%3A%22CHqLi9Z8H1AMnURmsALSNmxu0elpaj78%22%3B%7D",
    "sc": "75721E5D-DE17-5370-0389-943746C5B708",
    "cookies_policy": "true",
    "_csrf-api": "a115aeb71eb0eb2e9dce1fecb34afac32058e76f36f027a81f95325ccdb830b4a%3A2%3A%7Bi%3A0%3Bs%3A9%3A%22_csrf-api%22%3Bi%3A1%3Bs%3A32%3A%2207ihVY20DuEER2klf5L1ONGrPqwz3rUD%22%3B%7D",
    "v_cnt": "31",
    "device-source": "https://bi.ua/rus/product/prorezyvatel-taf-toys-sadik-v-gorode-ezhik-i-buryachok-13095.html",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    # 'cookie': 'device-referrer=https://www.google.com/; advanced-frontend=gsb71blijdi0183vuoh8b4i5ba; _csrf-frontend=55d068b1627cf15ff7363e11b6fbc4b27a348f3bfc77643eea3ac4671d5a3fd4a%3A2%3A%7Bi%3A0%3Bs%3A14%3A%22_csrf-frontend%22%3Bi%3A1%3Bs%3A32%3A%22CHqLi9Z8H1AMnURmsALSNmxu0elpaj78%22%3B%7D; sc=75721E5D-DE17-5370-0389-943746C5B708; cookies_policy=true; _csrf-api=a115aeb71eb0eb2e9dce1fecb34afac32058e76f36f027a81f95325ccdb830b4a%3A2%3A%7Bi%3A0%3Bs%3A9%3A%22_csrf-api%22%3Bi%3A1%3Bs%3A32%3A%2207ihVY20DuEER2klf5L1ONGrPqwz3rUD%22%3B%7D; v_cnt=31; device-source=https://bi.ua/rus/product/prorezyvatel-taf-toys-sadik-v-gorode-ezhik-i-buryachok-13095.html',
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "referer": "https://bi.ua/rus/dlya-malishey/pogremushki-prorezivateli/",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
}


# def load_proxies():
#     """Загружает список прокси-серверов из файла."""
#     with open(file_proxy, "r", encoding="utf-8") as file:
#         proxies = [line.strip() for line in file]
#     logger.info(f"Загружено {len(proxies)} прокси.")
#     return proxies


# def get_html():
#     proxies = load_proxies()  # Загружаем список всех прокси
#     proxy = random.choice(proxies)  # Выбираем случайный прокси
#     proxies_dict = {"http": proxy, "https": proxy}

#     response = requests.get(
#         "https://bi.ua/rus/product/prorezyvatel-nuby-zoopark-obezyanka-6733.html",
#         cookies=cookies,
#         headers=headers,
#         proxies=proxies_dict,
#     )

#     # Проверка кода ответа
#     if response.status_code == 200:
#         # Сохранение HTML-страницы целиком
#         with open("proba.html", "w", encoding="utf-8") as file:
#             file.write(response.text)
#     logger.info(response.status_code)


# def parsing():
#     proxies = load_proxies()  # Загружаем список всех прокси
#     proxy = random.choice(proxies)  # Выбираем случайный прокси
#     proxies_dict = {"http": proxy, "https": proxy}
#     with open("proba.html", encoding="utf-8") as file:
#         src = file.read()
#     soup = BeautifulSoup(src, "lxml")

#     # Список для хранения всех единиц данных
#     all_results = []
#     # Словарь для хранения параметров и их значений
#     params_variants = {}
#     # Безопасное извлечение заголовка страницы
#     name_raw = soup.find("h1", attrs={"itemprop": "name"})
#     page_title = name_raw.get_text(strip=True) if name_raw else None
#     description_raw = soup.find("article", attrs={"class": "scroller"})
#     product_code_raw = soup.find("span", attrs={"itemprop": "sku"})
#     product_code = product_code_raw.get_text(strip=True) if product_code_raw else None
#     price_raw = soup.find("div", attrs={"itemprop": "offers"}).find(
#         "p", attrs={"itemprop": "price"}
#     )
#     price = price_raw.get_text(strip=True).replace(" грн", "") if price_raw else None
#     old_price_raw = soup.find("div", attrs={"itemprop": "offers"}).find(
#         "p", attrs={"class": "old"}
#     )
#     old_price = (
#         old_price_raw.get_text(strip=True).replace(" грн", "")
#         if old_price_raw
#         else None
#     )
#     availability_text = None
#     stock_raw = soup.find("div", attrs={"class": "prodBuy blue"})
#     if stock_raw:
#         # Получаем текст ссылки и определяем статус наличия
#         availability_text = stock_raw.get_text(strip=True)
#         if "Купить" in availability_text:
#             availability_text = "В наличии"
#         elif "Товара нет в наличии" in availability_text:
#             availability_text = "Нет в наличии"
#     # Словарь для хранения параметров и их значений
#     params_variants = {}

#     # Переменная для отслеживания количества параметров
#     param_counter = 1

#     # Ищем все строки (tr) в таблицах
#     rows = soup.select("table.table.p03 tr")

#     # Перебираем все строки
#     for row in rows:
#         # Ищем все ячейки (td) в строке
#         cells = row.find_all("td")

#         # Пропускаем строки, которые содержат colspan (заголовки разделов)
#         if len(cells) == 2 and not cells[0].has_attr("colspan"):
#             param_name = cells[0].get_text(strip=True)  # Название параметра
#             variant_value = cells[1].get_text(strip=True)  # Значение параметра
#             # Добавляем в словарь
#             params_variants[f"param{param_counter}"] = param_name
#             params_variants[f"variant{param_counter}"] = variant_value
#             param_counter += 1
#     images = soup.find_all("img", attrs={"itemprop": "image"})
#     for images_url in images:
#         url_image = f'https://bi.ua{images_url.get("content")}'
#         try:
#             # Делаем запрос к URL
#             response = requests.get(
#                 url_image,
#                 cookies=cookies,
#                 headers=headers,
#                 proxies=proxies_dict,
#             )
#             response.raise_for_status()  # Проверяем, успешен ли запрос

#             # Извлекаем имя файла из URL
#             file_name = Path(url_image).name

#             # Путь для сохранения изображения
#             file_path = img_directory / file_name

#             # Сохраняем изображение
#             file_path.write_bytes(response.content)

#             logger.info(f"Сохранено: {file_path}")

#         except requests.exceptions.RequestException as e:
#             logger.error(f"Ошибка при загрузке {url_image}: {e}")


# if __name__ == "__main__":
# get_html()
# parsing()
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
        pattern = r"https://bi\.ua/sitemap_product(?:_\d+)?\.xml"
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
        # Фильтрация URL-ов, начинающихся с 'https://bi.ua/rus'
        filtered_urls = [
            loc.text for loc in locations if loc.text.startswith("https://bi.ua/rus")
        ]

        return filtered_urls

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
                # cookies=self.cookies,
            )

            # Проверяем успешность запроса
            if response.status_code == 200:

                # Сохраняем HTML-файл в указанную директорию
                file_path = self.html_files_directory / identifier
                # file_path = self.html_files_directory / f"{identifier}.html"
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


class Parsing:

    def __init__(self, html_files_directory, xlsx_result, file_proxy) -> None:
        self.html_files_directory = html_files_directory
        self.xlsx_result = xlsx_result
        self.file_proxy = file_proxy

    def load_proxies(self, file_proxy):
        # Загружаем список прокси-серверов из файла
        with open(self.file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        return proxies

    def parsing_html(self):
        proxies = self.load_proxies(file_proxy)
        # Выбираем случайный прокси-сервер для запроса
        proxy = random.choice(proxies)
        proxies_dict = {"http": proxy, "https": proxy}

        all_files = self.list_html()
        # Список для хранения всех единиц данных
        all_results = []
        for file_html in all_files:
            # Словарь для хранения параметров и их значений
            params_variants = {}
            logger.info(file_html)
            with open(file_html, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, "lxml")

            # Безопасное извлечение заголовка страницы
            name_raw = soup.find("h1", attrs={"itemprop": "name"})
            page_title = name_raw.get_text(strip=True) if name_raw else None

            # Ищем элемент с классом "scroller" внутри <article>
            description_raw = soup.find("article", attrs={"class": "scroller"})

            # Проверяем, найден ли элемент, и обрабатываем его содержимое
            if description_raw:
                description = re.sub(
                    r"\s+", " ", description_raw.decode_contents()
                ).strip()
            else:
                description = None  # Или другой текст по умолчанию, например, "Описание отсутствует"

            product_code_raw = soup.find("span", attrs={"itemprop": "sku"})
            product_code = (
                product_code_raw.get_text(strip=True) if product_code_raw else None
            )

            price_raw = soup.find("div", attrs={"itemprop": "offers"}).find(
                "p", attrs={"itemprop": "price"}
            )

            price = (
                price_raw.get_text(strip=True).replace(" грн", "")
                if price_raw
                else None
            )

            old_price_raw = soup.find("div", attrs={"itemprop": "offers"}).find(
                "p", attrs={"class": "old"}
            )
            old_price = (
                old_price_raw.get_text(strip=True).replace(" грн", "")
                if old_price_raw
                else None
            )

            availability_text = None
            stock_raw = soup.find("div", attrs={"class": "prodBuy blue"})
            if stock_raw:
                # Получаем текст ссылки и определяем статус наличия
                availability_text = stock_raw.get_text(strip=True)
                if "Купить" in availability_text:
                    availability_text = "В наличии"
                elif "Товара нет в наличии" in availability_text:
                    availability_text = "Нет в наличии"
                elif "Сообщить о наличии" in availability_text:
                    availability_text = "Нет в наличии"

            url = soup.find("meta", attrs={"itemprop": "item"}).get("content")

            # Пытаемся найти элемент <span> с атрибутом itemprop="brand", если не найден, ищем <a>
            brand_raw = soup.find("span", attrs={"itemprop": "brand"}) or soup.find(
                "a", attrs={"itemprop": "brand"}
            )

            # Если элемент найден, берем его текст, иначе устанавливаем None
            brand = brand_raw.get_text(strip=True) if brand_raw else None

            # Ищем все элементы с itemprop="name"
            table_bread = soup.find("div", attrs={"class": "breadcrWr"})
            breadcrumb_elements = table_bread.find_all(itemprop="name")

            # Убираем последний элемент из списка, если он существует
            if breadcrumb_elements:
                breadcrumb_elements = breadcrumb_elements[1:-1]

            # Создаем словарь для хранения breadcrumbs
            breadcrumbs = {}

            # Добавляем найденные значения в словарь с нужными ключами
            for i, element in enumerate(breadcrumb_elements):
                breadcrumbs[f"breadcrumbs{i+1}"] = element.get_text(strip=True)

            # Печатаем результаты
            for key, value in breadcrumbs.items():
                params_variants[key] = value
                # print(f"{key} = {value}")

            # Переменная для отслеживания количества параметров
            param_counter = 1

            # Ищем все строки (tr) в таблицах
            rows = soup.select("table.table.p03 tr")

            # Перебираем все строки
            for row in rows:
                # Ищем все ячейки (td) в строке
                cells = row.find_all("td")

                # Пропускаем строки, которые содержат colspan (заголовки разделов)
                if len(cells) == 2 and not cells[0].has_attr("colspan"):
                    param_name = cells[0].get_text(strip=True)  # Название параметра
                    variant_value = cells[1].get_text(strip=True)  # Значение параметра
                    # Добавляем в словарь
                    params_variants[f"param{param_counter}"] = param_name
                    params_variants[f"variant{param_counter}"] = variant_value
                    param_counter += 1
            images = soup.find_all("img", attrs={"itemprop": "image"})
            for index, images_url in enumerate(
                images, start=1
            ):  # start=1 начнет счетчик с 1
                url_image = f'https://bi.ua{images_url.get("content")}'
                # Извлекаем имя файла из URL
                file_name = Path(url_image).name
                # Добавляем файл в словарь с счетчиком
                params_variants[f"image{index}"] = file_name
                # Путь для сохранения изображения
                file_path = img_directory / file_name
                if not file_path.exists():
                    try:
                        # Делаем запрос к URL
                        response = requests.get(
                            url_image,
                            cookies=cookies,
                            headers=headers,
                            proxies=proxies_dict,
                        )
                        response.raise_for_status()  # Проверяем, успешен ли запрос

                        # Сохраняем изображение
                        file_path.write_bytes(response.content)

                        logger.info(f"Сохранено: {file_path}")

                    except requests.exceptions.RequestException as e:
                        logger.error(f"Ошибка при загрузке {url_image}: {e}")
            params_variants["name"] = page_title
            params_variants["description"] = description
            params_variants["product_code"] = product_code
            params_variants["brand"] = brand
            params_variants["stock"] = availability_text
            params_variants["url"] = url
            params_variants["old_price"] = old_price
            params_variants["price"] = price
            all_results.append(params_variants)
            # logger.info(params_variants)
        return all_results

    def list_html(self):
        # Получаем список всех файлов в директории
        file_list = [file for file in html_files_directory.iterdir() if file.is_file()]
        logger.info(len(file_list))
        return file_list

    # def write_to_excel(self, all_results):
    #     if not all_results:
    #         print("Нет данных для записи.")
    #         return

    #     df = pd.DataFrame(all_results)
    #     df.to_excel("output.xlsx", index=False, sheet_name="Data")


class WriteSQL:
    def __init__(self):
        # Загружаем переменные окружения из файла .env
        # Загружаем конфигурацию из .env файла
        load_dotenv(env_file_path)

        # Получаем параметры подключения
        self.db_host = os.getenv("DB_HOST")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")

        # Формируем URL для подключения
        self.database_url = f"mysql+aiomysql://{self.db_user}:{self.db_password}@{self.db_host}/{self.db_name}"

        # Создаем объект Database
        self.database = Database(self.database_url)

    async def connect(self):
        """Подключение к базе данных."""
        await self.database.connect()
        print("Успешное подключение к базе данных!")

    async def disconnect(self):
        """Отключение от базы данных."""
        await self.database.disconnect()
        print("Соединение с базой данных закрыто.")

    async def insert_data(self, table_name, data_list):
        """
        Вставляет список данных в таблицу базы данных, каждая запись (строка) - отдельный словарь из списка.

        :param table_name: Имя таблицы в базе данных.
        :param data_list: Список словарей, каждый из которых представляет строку для вставки.
        """
        logger.info(data_list)
        if not data_list:
            print("Нет данных для вставки.")
            return

        # Список всех столбцов, которые должны присутствовать в каждом словаре
        required_columns = [
            "name",
            "description",
            "product_code",
            "price",
            "old_price",
            "stock",
            "param1",
            "variant1",
            "param2",
            "variant2",
            "param3",
            "variant3",
            "param4",
            "variant4",
            "param5",
            "variant5",
            "param6",
            "variant6",
            "param7",
            "variant7",
            "param8",
            "variant8",
            "image1",
            "image2",
            "image3",
            "breadcrumbs1",
            "breadcrumbs2",
            "breadcrumbs3",
            "breadcrumbs4",
            "breadcrumbs6",
            "breadcrumbs7",
            "breadcrumbs8",
            "breadcrumbs9",
            "breadcrumbs10",
            "brand",
            "url",
            "categoryID",
            "category_name",
            "prosent",
            "mystock",
        ]

        # Обработка списка данных: заполняем все ключи значением None, если они отсутствуют
        # Обработка списка данных: заполняем все ключи значением None, если они отсутствуют
        for data in data_list:
            for column in required_columns:
                data.setdefault(column, None)

            # Устанавливаем значения по умолчанию для столбцов с ограничением NOT NULL
            for i in range(1, 9):  # Для param1 до param8 и variant1 до variant8
                if data[f"param{i}"] is None:
                    data[f"param{i}"] = "N/A"
                if data[f"variant{i}"] is None:
                    data[f"variant{i}"] = "N/A"

            for i in range(1, 4):  # Для image1 до image3
                if data[f"image{i}"] is None:
                    data[f"image{i}"] = "N/A"

            for i in [1, 2, 3, 4, 6, 7, 8, 9, 10]:  # Исключаем 5
                if data[f"breadcrumbs{i}"] is None:
                    data[f"breadcrumbs{i}"] = 0

            # Устанавливаем значения по умолчанию для остальных столбцов
            if data["price"] is None:
                data["price"] = 0
            if data["product_code"] is None:
                data["product_code"] = 0
            if data["name"] is None:
                data["name"] = "No Name"
            if data["stock"] is None:
                data["stock"] = "Unknown"
            if data["categoryID"] is None:
                data["categoryID"] = 0
            if data["prosent"] is None:
                data["prosent"] = "0"
            if data["mystock"] is None:
                data["mystock"] = 0
            if data["url"] is None:
                data["url"] = "N/A"
            if data["description"] is None:
                data["description"] = "No description"
            if data["brand"] is None:
                data["brand"] = "Unknown"
            if data["category_name"] is None:
                data["category_name"] = "Unknown"

        # Получаем список всех столбцов из первого элемента списка
        columns = ", ".join(required_columns)
        placeholders = ", ".join([f":{key}" for key in required_columns])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        # Обработка списка данных
        try:
            # Вставка всех данных, каждый словарь - отдельная строка
            await self.database.execute_many(query=query, values=data_list)
            print(f"Успешно вставлено {len(data_list)} записей!")
        except Exception as e:
            print(f"Ошибка при вставке данных: {e}")


max_workers = 10
base_url = "https://www.ua-region.com.ua"
url_sitemap = "https://bi.ua/sitemap-index.xml"
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

# Запуск метода скачивания html файлов
# response_handler.process_infox_file()


# Парсинг html файлов
processor = Parsing(html_files_directory, xlsx_result, file_proxy)
all_results = processor.parsing_html()


async def main(all_results):
    # Использование класса WriteSQL
    write_sql = WriteSQL()
    await write_sql.connect()
    await write_sql.insert_data("ss_bi", all_results)
    await write_sql.disconnect()


asyncio.run(main(all_results))

# write_sql = WriteSQL()
# write_sql.insert_data("ss_bi", all_results)
# write_sql.close_connection()
