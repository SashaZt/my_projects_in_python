import csv
import random
import re
import sys
import threading
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)
from tqdm import tqdm
from working_with_files import Working_with_files

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
file_proxy = configuration_directory / "proxy.txt"


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

        try:
            # Запрос по указанному URL с отключенной проверкой SSL
            response = requests.get(
                url,
                proxies=proxies_dict,
                headers=self.headers,
                # cookies=self.cookies,
                verify=False,  # Отключаем проверку SSL
                timeout=30,
            )

            if response.status_code == 200:
                logger.info(f"Скачали sitemap: {url}")
                return response.content
            else:
                logger.error(f"Ошибка при скачивании файла: {
                    response.status_code} для URL: {url}")
                return None

        except requests.exceptions.SSLError as ssl_error:
            logger.error(f"SSL ошибка для URL {url}: {ssl_error}")
            return None

        except requests.exceptions.MaxRetryError as retry_error:
            logger.error(f"Ошибка переподключения для URL {
                         url}: {retry_error}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Произошла ошибка при запросе URL {url}: {e}")
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
        matching_urls = [
            loc.text for loc in locations if re.match(pattern, loc.text)]
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
            futures = []
            for url in urls_df["url"]:
                # Определяем идентификатор и путь к файлу
                identifier = url.split("/")[-1]
                file_path = self.html_files_directory / f"{identifier}.html"

                # Пропускаем URL, если файл уже существует
                if file_path.exists():
                    logger.info(f"Файл уже существует для URL: {
                                url}, пропускаем.")
                    progress_bar.update(1)
                    continue

                # Добавляем задачу в executor, передавая file_path
                futures.append(executor.submit(
                    self.fetch_and_save_html, url, file_path, successful_urls, proxies))

            # Отслеживаем выполнение задач
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error occurred: {e}")
                finally:
                    progress_bar.update(1)

        # Закрываем прогресс-бар
        progress_bar.close()

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_fixed(30),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def fetch_and_save_html(self, url, file_path, successful_urls, proxies):
        fetch_lock = threading.Lock()

        # Прерываем выполнение, если установлено событие остановки
        if self.stop_event.is_set():
            return

        # Проверка, обрабатывался ли URL ранее
        if url in successful_urls:
            logger.info("| Компания уже была обработана, пропускаем. |")
            return

        try:
            proxy = random.choice(proxies)
            proxies_dict = {"http": proxy, "https": proxy}

            # Запрос к серверу
            response = requests.get(
                url,
                headers=self.headers,
                proxies=proxies_dict,
                timeout=30,
                cookies=self.cookies,
                verify=False  # Отключаем проверку SSL
            )

            # Если статус код ошибки >= 400, фиксируем ошибку и исключаем повторные попытки
            if response.status_code >= 400:
                if response.status_code == 404:
                    logger.warning(f"URL не найден (404): {url}")
                    return  # Прекращаем дальнейшие попытки на 404
                raise requests.HTTPError(
                    f"Статус: {response.status_code} для URL: {url}",
                    response=response,
                )
            if response.status_code == 429:
                retry_after = int(
                    response.headers.get("Retry-After", 60)
                )  # Ждем 60 секунд по умолчанию
                sys.exit(1)  # Останавливаем весь процесс

            # Проверка содержимого и запись HTML
            if response.status_code == 200 and "text/html" in response.headers.get(
                "Content-Type", ""
            ):
                file_path.write_text(response.text, encoding="utf-8")

                with fetch_lock:
                    successful_urls.add(url)

                # Обновляем CSV-файл для отслеживания успешных
                self.working_files.write_to_csv(url, self.csv_file_successful)
            else:
                logger.error(f"Некорректный тип содержимого для URL: {url}")
                raise requests.HTTPError(
                    f"Некорректный тип содержимого для URL: {url}",
                    response=response,
                )

        except requests.RequestException as e:
            logger.error(f"Ошибка при обработке запроса для URL {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Произошла ошибка при обработке {url}: {e}")
