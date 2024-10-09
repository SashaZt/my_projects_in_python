import requests
from configuration.logger_setup import logger
from bs4 import BeautifulSoup
from tqdm import tqdm
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
import hashlib
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type


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
file_proxy = configuration_directory / "roman.txt"
csv_file_successful = data_directory / "identifier_successful.csv"
xlsx_result = data_directory / "result.xlsx"
# Создаем путь к файлу .env
env_file_path = configuration_directory / ".env"

# Загружаем переменные окружения из файла .env
load_dotenv(env_file_path)

cookies = {
    # "advanced-frontend": "kmisddorok18b7il8f76g5ln8k",
    # "_csrf-frontend": "61fb553d2b51ca0f76a29c9d37829abc59a9c2b402a694b99cd506556776b276a%3A2%3A%7Bi%3A0%3Bs%3A14%3A%22_csrf-frontend%22%3Bi%3A1%3Bs%3A32%3A%22kMjThColddL8RX48yd7xr48HiaAxOuuh%22%3B%7D",
    # "sbjs_migrations": "1418474375998%3D1",
    # "sbjs_current_add": "fd%3D2024-10-07%2008%3A19%3A03%7C%7C%7Cep%3Dhttps%3A%2F%2Fbi.ua%2Fukr%2F%7C%7C%7Crf%3D%28none%29",
    # "sbjs_first_add": "fd%3D2024-10-07%2008%3A19%3A03%7C%7C%7Cep%3Dhttps%3A%2F%2Fbi.ua%2Fukr%2F%7C%7C%7Crf%3D%28none%29",
    # "sbjs_current": "typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29",
    # "sbjs_first": "typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29",
    # "sbjs_udata": "vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F129.0.0.0%20Safari%2F537.36",
    # "_gcl_au": "1.1.1529364144.1728278344",
    # "_gid": "GA1.2.1597231364.1728278344",
    # "_fbp": "fb.1.1728278343842.92381071656458803",
    # "_dc_gtm_UA-8203486-4": "1",
    # "sc": "293DACE4-B736-4DDB-9351-897190C8C3BF",
    # "_hjSession_1559188": "eyJpZCI6ImRhMDlkN2QzLTZhMmMtNGUyYy04NDFmLWFiYjExN2Q1Zjc3NyIsImMiOjE3MjgyNzgzNDM5MDQsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxfQ==",
    # "__rtbh.uid": "%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22unknown%22%7D",
    # "__rtbh.lid": "%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22FbjuS45AulssEOPF8b9x%22%7D",
    # "_p_uid": "uid-442ed1e03.3a8ba833c.47efbbd2e",
    # "clickanalyticsresource": "f5346240-88b6-4b20-8e99-903ed54a056f",
    # "device-source": "https://bi.ua/ukr/",
    # "device-referrer": "",
    # "sbjs_session": "pgs%3D2%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fbi.ua%2Fukr%2F",
    # "_ga_71EP10GZSQ": "GS1.1.1728278343.1.1.1728278364.39.0.533920916",
    # "_hjSessionUser_1559188": "eyJpZCI6IjI0MDQ4NjkwLTU3MmItNTUyMC04NzE3LTM1NWU4NWQ1YzU3YiIsImNyZWF0ZWQiOjE3MjgyNzgzNDM5MDIsImV4aXN0aW5nIjp0cnVlfQ==",
    "_ga": "GA1.2.1752615101.1728278344",
    "cookies_policy": "true",
    # "_gali": "cookie_note",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
}


class GetResponse:

    def __init__(
        self,
        max_workers,
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
        self.working_files = WorkingWithfiles(
            self.csv_file_successful, output_csv_file, self.file_proxy
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def fetch_xml(self, url):
        # Загружаем список прокси-серверов из файла
        proxies = self.working_files.load_proxies()
        # Выбираем случайный прокси-сервер для запроса
        if not proxies:
            logger.error("Список прокси пуст. Проверьте файл с прокси.")
            return None
        proxy = random.choice(proxies)
        # proxy = random.choice(proxies)
        proxies_dict = {"http": proxy, "https": proxy}

        # Запрос по указанному URL
        response = requests.get(
            url,
            proxies=proxies_dict,
            headers=self.headers,
            cookies=self.cookies,
            timeout=10,
        )
        response.raise_for_status()
        if "text/xml" in response.headers.get("Content-Type", ""):
            logger.info(f"Скачали sitemap: {url}")
            return response.content
        # if response.status_code == 200:
        #     logger.info(f"Скачали sitemap: {url}")
        #     return response.content
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

    def process_html_files(self):
        self.working_files.remove_successful_urls()
        proxies = self.working_files.load_proxies()
        successful_urls = self.working_files.get_successful_urls()
        urls_df = pd.read_csv(self.output_csv_file)
        total_urls = len(urls_df)
        progress_bar = tqdm(
            total=total_urls,
            desc="Обработка файлов",
            bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
        )

        max_failures = 5
        failure_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self.fetch_and_save_html, url, successful_urls, proxies)
                for url in urls_df["url"]
            ]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error occurred: {e}")
                    failure_count += 1
                    if failure_count >= max_failures:
                        logger.error(
                            "Превышен лимит неудачных операций. Остановка выполнения."
                        )
                        self.stop_event.set()
                        break
                finally:
                    progress_bar.update(1)

        progress_bar.close()
        if self.stop_event.is_set():
            logger.error("Программа остановлена из-за ошибок.")
            sys.exit(1)
        else:
            logger.info("Все файлы скаченны.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type(requests.RequestException),
    )
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
        # Генерируем короткое имя файла, используя хеширование
        hash_object = hashlib.md5(identifier.encode("utf-8"))

        hashed_filename = hash_object.hexdigest() + ".html"
        hashed_file_path = self.html_files_directory / hashed_filename
        try:
            # Выбираем случайный прокси-сервер для запроса
            proxy = random.choice(proxies)
            proxies_dict = {"http": proxy, "https": proxy}

            # Отправляем запрос, если файл еще не существует
            if not hashed_file_path.exists():
                response = requests.get(
                    url,
                    proxies=proxies_dict,
                    headers=self.headers,
                    cookies=self.cookies,
                    timeout=10,
                )

                # Проверка статуса, если не успешный (3xx, 4xx, 5xx), инициируем повторную попытку

                if response.status_code >= 300:
                    logger.warning(
                        f"Получили статус {response.status_code} для URL: {url}, пробуем еще раз."
                    )
                    raise requests.HTTPError(
                        f"Статус: {response.status_code} для URL: {url}",
                        response=response,
                    )

                if response.status_code == 200:
                    if "text/html" in response.headers.get("Content-Type", ""):
                        hashed_file_path.write_text(response.text, encoding="utf-8")
                        # logger.info(f"Скачали и сохранили HTML для {url}")
                    else:
                        logger.error(f"Ошибка: некорректный тип содержимого для {url}")
                        raise requests.HTTPError(
                            f"Статус: {response.status_code} для URL: {url}",
                            response=response,
                        )
                else:
                    logger.warning(
                        f"Получили статус {response.status_code} для URL: {url}, пробуем еще раз."
                    )
                    raise requests.HTTPError(
                        f"Статус: {response.status_code} для URL: {url}",
                        response=response,
                    )

        except requests.RequestException as e:
            logger.error(f"Ошибка при скачивании файла: {e}")
            raise  # Повторная попытка будет выполнена, так как исключение RequestException включено в retry
        except Exception as e:
            logger.error(f"Произошла ошибка при обработке {url}: {e}")
            self.stop_event.set()  # Устанавливаем событие остановки


class WorkingWithfiles:

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
        file_path = Path(filename)
        with self.write_lock:
            # Проверка на необходимость добавления заголовка, если файл только создается или пустой
            if not self.header_written:
                if not file_path.exists() or file_path.stat().st_size == 0:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write("url\n")
                self.header_written = True

            # Записываем данные в файл
            urls_to_write = data if isinstance(data, (set, list, tuple)) else [data]
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
                row[0]
                for idx, row in enumerate(reader)
                if row and idx > 0  # Пропускаем заголовок
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

    def __init__(
        self, html_files_directory, xlsx_result, file_proxy, max_workers
    ) -> None:
        self.html_files_directory = html_files_directory
        self.xlsx_result = xlsx_result
        self.file_proxy = file_proxy
        self.max_workers = max_workers  # Максимальное количество потоков

    def load_proxies(self):
        # Загружаем список прокси-серверов из файла
        with open(self.file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        return proxies

    def parse_single_html(self, file_html):
        params_variants = {}
        proxies = self.load_proxies()
        # Выбираем случайный прокси-сервер для запроса
        proxy = random.choice(proxies)
        proxies_dict = {"http": proxy, "https": proxy}
        # Словарь для хранения параметров и их значений

        # logger.info(file_html)
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
            description = re.sub(r"\s+", " ", description_raw.decode_contents()).strip()
        else:
            description = (
                None  # Или другой текст по умолчанию, например, "Описание отсутствует"
            )

        product_code_raw = soup.find("span", attrs={"itemprop": "sku"})
        product_code = (
            product_code_raw.get_text(strip=True) if product_code_raw else None
        )

        price_raw = soup.find("div", attrs={"itemprop": "offers"}).find(
            "p", attrs={"itemprop": "price"}
        )
        if price_raw:
            # Удаляем нецифровые символы и пробелы из текста
            price_text = re.sub(r"[^\d]", "", price_raw.get_text(strip=True))
            # Преобразуем в целое число, если удалось найти цифры, иначе 0
            price = int(price_text) if price_text else 0
        else:
            price = 0

        # Извлечение и обработка old_price
        old_price_raw = soup.find("div", attrs={"itemprop": "offers"}).find(
            "p", attrs={"class": "old"}
        )
        if old_price_raw:
            # Удаляем нецифровые символы и пробелы из текста
            old_price_text = re.sub(r"[^\d]", "", old_price_raw.get_text(strip=True))
            # Преобразуем в целое число, если удалось найти цифры, иначе 0
            old_price = int(old_price_text) if old_price_text else 0
        else:
            old_price = 0

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
        # Ограничение на количество загружаемых изображений (не больше 3)
        max_images = 3
        for index, images_url in enumerate(images, start=1):
            if index > max_images:  # Прерываем цикл, если уже обработано 3 изображения
                break
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
        return params_variants

    def parsing_html(self):
        # Получаем список HTML файлов
        all_files = self.list_html()

        # Инициализация прогресс-бара
        total_urls = len(all_files)
        progress_bar = tqdm(
            total=total_urls,
            desc="Обработка файлов",
            bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
        )

        # Многопоточная обработка файлов
        all_results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.parse_single_html, file_html): file_html
                for file_html in all_files
            }

            # Сбор результатов по мере завершения каждого потока
            for future in as_completed(futures):
                file_html = futures[future]
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    logger.error(f"Ошибка при обработке файла {file_html}: {e}")
                finally:
                    # Обновляем прогресс-бар после завершения обработки каждого файла
                    progress_bar.update(1)

        # Закрываем прогресс-бар
        progress_bar.close()

        return all_results

    # def parsing_html(self):

    #     all_files = self.list_html()
    #     # Список для хранения всех единиц данных
    #     all_results = []
    #     for file_html in all_files:
    #         params_variants = {}
    #         proxies = self.load_proxies()
    #         # Выбираем случайный прокси-сервер для запроса
    #         proxy = random.choice(proxies)
    #         proxies_dict = {"http": proxy, "https": proxy}
    #         # Словарь для хранения параметров и их значений

    #         # logger.info(file_html)
    #         with open(file_html, encoding="utf-8") as file:
    #             src = file.read()
    #         soup = BeautifulSoup(src, "lxml")

    #         # Безопасное извлечение заголовка страницы
    #         name_raw = soup.find("h1", attrs={"itemprop": "name"})
    #         page_title = name_raw.get_text(strip=True) if name_raw else None

    #         # Ищем элемент с классом "scroller" внутри <article>
    #         description_raw = soup.find("article", attrs={"class": "scroller"})

    #         # Проверяем, найден ли элемент, и обрабатываем его содержимое
    #         if description_raw:
    #             description = re.sub(
    #                 r"\s+", " ", description_raw.decode_contents()
    #             ).strip()
    #         else:
    #             description = None  # Или другой текст по умолчанию, например, "Описание отсутствует"

    #         product_code_raw = soup.find("span", attrs={"itemprop": "sku"})
    #         product_code = (
    #             product_code_raw.get_text(strip=True) if product_code_raw else None
    #         )

    #         price_raw = soup.find("div", attrs={"itemprop": "offers"}).find(
    #             "p", attrs={"itemprop": "price"}
    #         )
    #         if price_raw:
    #             # Удаляем нецифровые символы и пробелы из текста
    #             price_text = re.sub(r"[^\d]", "", price_raw.get_text(strip=True))
    #             # Преобразуем в целое число, если удалось найти цифры, иначе 0
    #             price = int(price_text) if price_text else 0
    #         else:
    #             price = 0

    #         # Извлечение и обработка old_price
    #         old_price_raw = soup.find("div", attrs={"itemprop": "offers"}).find(
    #             "p", attrs={"class": "old"}
    #         )
    #         if old_price_raw:
    #             # Удаляем нецифровые символы и пробелы из текста
    #             old_price_text = re.sub(
    #                 r"[^\d]", "", old_price_raw.get_text(strip=True)
    #             )
    #             # Преобразуем в целое число, если удалось найти цифры, иначе 0
    #             old_price = int(old_price_text) if old_price_text else 0
    #         else:
    #             old_price = 0

    #         availability_text = None
    #         stock_raw = soup.find("div", attrs={"class": "prodBuy blue"})
    #         if stock_raw:
    #             # Получаем текст ссылки и определяем статус наличия
    #             availability_text = stock_raw.get_text(strip=True)
    #             if "Купить" in availability_text:
    #                 availability_text = "В наличии"
    #             elif "Товара нет в наличии" in availability_text:
    #                 availability_text = "Нет в наличии"
    #             elif "Сообщить о наличии" in availability_text:
    #                 availability_text = "Нет в наличии"

    #         url = soup.find("meta", attrs={"itemprop": "item"}).get("content")

    #         # Пытаемся найти элемент <span> с атрибутом itemprop="brand", если не найден, ищем <a>
    #         brand_raw = soup.find("span", attrs={"itemprop": "brand"}) or soup.find(
    #             "a", attrs={"itemprop": "brand"}
    #         )

    #         # Если элемент найден, берем его текст, иначе устанавливаем None
    #         brand = brand_raw.get_text(strip=True) if brand_raw else None

    #         # Ищем все элементы с itemprop="name"
    #         table_bread = soup.find("div", attrs={"class": "breadcrWr"})
    #         breadcrumb_elements = table_bread.find_all(itemprop="name")

    #         # Убираем последний элемент из списка, если он существует
    #         if breadcrumb_elements:
    #             breadcrumb_elements = breadcrumb_elements[1:-1]

    #         # Создаем словарь для хранения breadcrumbs
    #         breadcrumbs = {}

    #         # Добавляем найденные значения в словарь с нужными ключами
    #         for i, element in enumerate(breadcrumb_elements):
    #             breadcrumbs[f"breadcrumbs{i+1}"] = element.get_text(strip=True)

    #         # Печатаем результаты
    #         for key, value in breadcrumbs.items():
    #             params_variants[key] = value
    #             # print(f"{key} = {value}")

    #         # Переменная для отслеживания количества параметров
    #         param_counter = 1

    #         # Ищем все строки (tr) в таблицах
    #         rows = soup.select("table.table.p03 tr")

    #         # Перебираем все строки
    #         for row in rows:
    #             # Ищем все ячейки (td) в строке
    #             cells = row.find_all("td")

    #             # Пропускаем строки, которые содержат colspan (заголовки разделов)
    #             if len(cells) == 2 and not cells[0].has_attr("colspan"):
    #                 param_name = cells[0].get_text(strip=True)  # Название параметра
    #                 variant_value = cells[1].get_text(strip=True)  # Значение параметра
    #                 # Добавляем в словарь
    #                 params_variants[f"param{param_counter}"] = param_name
    #                 params_variants[f"variant{param_counter}"] = variant_value
    #                 param_counter += 1
    #         images = soup.find_all("img", attrs={"itemprop": "image"})
    #         # Ограничение на количество загружаемых изображений (не больше 3)
    #         max_images = 3
    #         for index, images_url in enumerate(images, start=1):
    #             if (
    #                 index > max_images
    #             ):  # Прерываем цикл, если уже обработано 3 изображения
    #                 break
    #             url_image = f'https://bi.ua{images_url.get("content")}'
    #             # Извлекаем имя файла из URL
    #             file_name = Path(url_image).name
    #             # Добавляем файл в словарь с счетчиком
    #             params_variants[f"image{index}"] = file_name
    #             # Путь для сохранения изображения
    #             file_path = img_directory / file_name
    #             if not file_path.exists():
    #                 try:
    #                     # Делаем запрос к URL
    #                     response = requests.get(
    #                         url_image,
    #                         cookies=cookies,
    #                         headers=headers,
    #                         proxies=proxies_dict,
    #                     )
    #                     response.raise_for_status()  # Проверяем, успешен ли запрос

    #                     # Сохраняем изображение
    #                     file_path.write_bytes(response.content)

    #                     logger.info(f"Сохранено: {file_path}")

    #                 except requests.exceptions.RequestException as e:
    #                     logger.error(f"Ошибка при загрузке {url_image}: {e}")
    #         params_variants["name"] = page_title
    #         params_variants["description"] = description
    #         params_variants["product_code"] = product_code
    #         params_variants["brand"] = brand
    #         params_variants["stock"] = availability_text
    #         params_variants["url"] = url
    #         params_variants["old_price"] = old_price
    #         params_variants["price"] = price
    #         all_results.append(params_variants)
    #         # logger.info(params_variants)
    #     return all_results

    def list_html(self):
        # Получаем список всех файлов в директории
        file_list = [file for file in html_files_directory.iterdir() if file.is_file()]
        # logger.info(len(file_list))
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

    async def fetch_product_codes(self):
        """
        Извлекает колонки 'product_code' из таблицы.

        :return: Список product_code из базы данных.
        """
        query = "SELECT product_code FROM ss_bi"
        try:
            results = await self.database.fetch_all(query=query)
            # Извлекаем только значения 'product_code' в виде списка
            product_codes = [record["product_code"] for record in results]
            return product_codes
        except Exception as e:
            print(f"Ошибка при извлечении данных: {e}")
            return []

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
        Вставляет или обновляет список данных в таблицу базы данных.
        :param table_name: Имя таблицы в базе данных.
        :param data_list: Список словарей, каждый из которых представляет строку для вставки.
        """
        if not data_list:
            print("Нет данных для вставки.")
            return

        # Получаем текущие записи в базе данных по product_code
        existing_data = await self.fetch_product_codes()
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

        # Разделяем данные для вставки и обновления
        data_to_update = []
        data_to_insert = []
        for data in data_list:
            product_code = (
                int(data.get("product_code")) if data.get("product_code") else None
            )

            if product_code in existing_data:
                # Если товар существует, добавляем его в список для обновления
                data_to_update.append(
                    {
                        "product_code": product_code,
                        "stock": data.get("stock", "Unknown"),
                        "price": data.get("price", 0),
                    }
                )
            else:
                logger.info(f"Товар нет в таблице {product_code}")
                # Отфильтруем и подготовим данные для вставки
                filtered_data = {key: data.get(key, None) for key in required_columns}

                # Устанавливаем значения по умолчанию для обязательных полей
                for i in range(1, 9):  # Для param1 до param8 и variant1 до variant8
                    if filtered_data[f"param{i}"] is None:
                        filtered_data[f"param{i}"] = "N/A"
                    if filtered_data[f"variant{i}"] is None:
                        filtered_data[f"variant{i}"] = "N/A"

                for i in range(1, 4):  # Для image1 до image3
                    if filtered_data[f"image{i}"] is None:
                        filtered_data[f"image{i}"] = "N/A"

                for i in [
                    1,
                    2,
                    3,
                    4,
                    6,
                    7,
                    8,
                    9,
                    10,
                ]:  # Для breadcrumbs1 до breadcrumbs4 и breadcrumbs6 до breadcrumbs10
                    if filtered_data[f"breadcrumbs{i}"] is None:
                        filtered_data[f"breadcrumbs{i}"] = "N/A"

                # Значения по умолчанию для остальных полей
                filtered_data["price"] = (
                    0 if not filtered_data["price"] else filtered_data["price"]
                )
                filtered_data["old_price"] = (
                    0 if not filtered_data["old_price"] else filtered_data["old_price"]
                )
                filtered_data["product_code"] = (
                    0
                    if not filtered_data["product_code"]
                    else filtered_data["product_code"]
                )
                filtered_data["categoryID"] = (
                    0
                    if not filtered_data["categoryID"]
                    else filtered_data["categoryID"]
                )
                filtered_data["mystock"] = (
                    0 if not filtered_data["mystock"] else filtered_data["mystock"]
                )

                filtered_data["name"] = (
                    "No Name"
                    if filtered_data["name"] is None
                    else filtered_data["name"]
                )
                filtered_data["stock"] = (
                    "Unknown"
                    if filtered_data["stock"] is None
                    else filtered_data["stock"]
                )
                filtered_data["prosent"] = (
                    "0"
                    if filtered_data["prosent"] is None
                    else filtered_data["prosent"]
                )
                filtered_data["url"] = (
                    "N/A" if filtered_data["url"] is None else filtered_data["url"]
                )
                filtered_data["description"] = (
                    "No description"
                    if filtered_data["description"] is None
                    else filtered_data["description"]
                )
                filtered_data["brand"] = (
                    "Unknown"
                    if filtered_data["brand"] is None
                    else filtered_data["brand"]
                )
                filtered_data["category_name"] = (
                    "Unknown"
                    if filtered_data["category_name"] is None
                    else filtered_data["category_name"]
                )

                # Добавляем в список для вставки
                data_to_insert.append(filtered_data)

        # Выполняем обновление существующих товаров
        for item in data_to_update:
            update_query = f"""
                UPDATE {table_name} 
                SET stock = :stock, price = :price 
                WHERE product_code = :product_code
            """
            try:
                await self.database.execute(query=update_query, values=item)
                logger.info(f"Обновлена запись с product_code: {item['product_code']}")
            except Exception as e:
                logger.error(f"Ошибка при обновлении данных: {e}")

        # Выполняем вставку новых товаров
        if data_to_insert:
            columns = ", ".join(required_columns)
            placeholders = ", ".join([f":{key}" for key in required_columns])
            insert_query = (
                f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            )
            try:
                await self.database.execute_many(
                    query=insert_query, values=data_to_insert
                )
                logger.info(f"Успешно вставлено {len(data_to_insert)} записей!")
            except Exception as e:
                logger.error(f"Ошибка при вставке данных: {e}")


max_workers = 20
url_sitemap = "https://bi.ua/sitemap-index.xml"
response_handler = GetResponse(
    max_workers,
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
response_handler.process_html_files()


# Парсинг html файлов
processor = Parsing(html_files_directory, xlsx_result, file_proxy, max_workers)
all_results = processor.parsing_html()


async def main(all_results):
    # Использование класса WriteSQL
    write_sql = WriteSQL()
    await write_sql.connect()
    await write_sql.insert_data("ss_bi", all_results)
    await write_sql.disconnect()


asyncio.run(main(all_results))
