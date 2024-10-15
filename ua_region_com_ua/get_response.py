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
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import shutil
import traceback
import sqlite3
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
# file_proxy = configuration_directory / "roman.txt"


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
            url,
            proxies=proxies_dict,
            headers=self.headers,
            cookies=self.cookies,
            timeout=10,
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
                    # self.stop_event.set()  # Устанавливаем событие для остановки всех потоков

                finally:
                    # Обновляем прогресс-бар после каждой завершенной задачи
                    progress_bar.update(1)

        # Закрываем прогресс-бар
        progress_bar.close()
        # if self.stop_event.is_set():
        #     logger.error("Программа остановлена из-за ошибок.")
        #     sys.exit(1)
        # else:
        #     logger.info("Все запросы выполнены.")

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
            logger.info("| Компания уже была обработана, пропускаем. |")
            return
        identifier = url.split("/")[-1]
        try:
            # Выбираем случайный прокси-сервер для запроса
            proxy = random.choice(proxies)
            proxies_dict = {"http": proxy, "https": proxy}
            # Отправляем запрос
            response = requests.get(
                url,
                # proxies=proxies_dict,
                headers=self.headers,
                timeout=10,
                # cookies=self.cookies,
            )
            if response.status_code >= 300:
                # logger.warning(
                #     f"Получили статус {response.status_code} для URL: {url}, пробуем еще раз."
                # )
                raise requests.HTTPError(
                    f"Статус: {response.status_code} для URL: {url}",
                    response=response,
                )

            # Проверяем успешность запроса
            if response.status_code == 200:
                if "text/html" in response.headers.get("Content-Type", ""):
                    # Сохраняем HTML-файл в указанную директорию
                    file_path = self.html_files_directory / f"{identifier}.html"
                    file_path.write_text(response.text, encoding="utf-8")
                    with fetch_lock:
                        # Добавляем идентификатор в множество успешных
                        successful_urls.add(url)

                    # Сохраняем идентификатор в CSV для отслеживания
                    self.working_files.write_to_csv(url, self.csv_file_successful)
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
            # logger.error(f"Ошибка при скачивании файла: {e}")
            raise  # Повторная попытка будет выполнена, так как исключение RequestException включено в retry
        except Exception as e:
            logger.error(f"Произошла ошибка при обработке {url}: {e}")
            # self.stop_event.set()  # Устанавливаем событие остановки
