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
import urllib3
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
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

# Отключаем предупреждение InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GetResponse:
    NAMESPACE = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    def __init__(
        self,
        max_workers,
        base_url,
        headers,
        html_files_directory,
        csv_file_successful,
        output_csv_file,
        file_proxy,
        url_sitemap,
    ) -> None:
        self.max_workers = max_workers
        self.base_url = base_url
        self.headers = headers
        self.html_files_directory = Path(html_files_directory)
        self.csv_file_successful = csv_file_successful
        self.output_csv_file = output_csv_file
        self.file_proxy = file_proxy
        self.url_sitemap = url_sitemap
        self.stop_event = threading.Event()
        self.working_files = Working_with_files(
            self.csv_file_successful, output_csv_file, self.file_proxy
        )

    def _choose_proxy(self):
        proxies = self.working_files.load_proxies()
        proxy = random.choice(proxies)
        return {"http": proxy, "https": proxy}

    def fetch_xml(self, url):
        proxies_dict = self._choose_proxy()
        try:
            response = requests.get(
                url,
                proxies=proxies_dict,
                headers=self.headers,
                verify=False,
                timeout=30,
            )
            if response.status_code == 200:
                logger.info(f"Скачали sitemap: {url}")
                return response.content
            else:
                logger.error(
                    f"Ошибка при скачивании файла: {response.status_code} для URL: {url}"
                )
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе URL {url}: {e}")
            return None

    def get_sitemap_start(self):
        return self.fetch_xml(self.url_sitemap)

    def parsing_sitemap_start(self):
        content = self.get_sitemap_start()
        if content:
            return self.parsing_sitemap(content)
        return []

    def parsing_sitemap(self, content):
        """
        Парсит файл sitemapindex и возвращает список ссылок на файлы sitemap.
        """
        root = ET.fromstring(content)
        locations = root.findall(".//ns:loc", self.NAMESPACE)
        return [loc.text for loc in locations]

    def get_all_sitemap(self):
        all_url_company = set()
        all_urls = self.parsing_sitemap_start()
        for url in all_urls:
            content = self.fetch_xml(url)
            if content:
                urls_company = self.parsing_all_sitemap(content)
                all_url_company.update(urls_company)
            else:
                logger.error(f"Ошибка при обработке URL: {url}")
        logger.info(len(all_url_company))
        self.working_files.write_to_csv(all_url_company, self.output_csv_file)

    def parsing_all_sitemap(self, content):
        """
        Парсит файл urlset и возвращает список всех URL.
        """
        root = ET.fromstring(content)
        locations = root.findall(".//ns:loc", self.NAMESPACE)
        return [loc.text for loc in locations]

    def process_infox_file(self):
        self.working_files.remove_successful_urls()
        successful_urls = self.working_files.get_successful_urls()
        urls_df = pd.read_csv(self.output_csv_file)
        total_urls = len(urls_df)
        progress_bar = tqdm(total=total_urls, desc="Обработка файлов")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for url in urls_df["url"]:
                identifier = url.split("/")[-2]
                file_path = self.html_files_directory / f"{identifier}.html"

                if file_path.exists():
                    logger.info(f"Файл уже существует для URL: {url}, пропускаем.")
                    progress_bar.update(1)
                    continue

                futures.append(
                    executor.submit(
                        self.fetch_and_save_html, url, file_path, successful_urls
                    )
                )

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error occurred: {e}")
                finally:
                    progress_bar.update(1)

        progress_bar.close()

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_fixed(30),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def fetch_and_save_html(self, url, file_path, successful_urls):
        fetch_lock = threading.Lock()

        if self.stop_event.is_set():
            return

        if url in successful_urls:
            logger.info("| Компания уже была обработана, пропускаем. |")
            return

        try:
            proxies_dict = (
                self._choose_proxy()
            )  # Теперь используем _choose_proxy напрямую

            # # Прокси-сервер
            # proxy = "37.48.118.4:13010"

            # # Настройки прокси для requests
            # proxies = {
            #     "http": f"http://{proxy}",
            #     "https": f"http://{proxy}",
            # }
            response = requests.get(
                url,
                headers=self.headers,
                proxies=proxies_dict,
                timeout=30,
                verify=False,
            )

            # if response.status_code >= 400:
            #     if response.status_code == 404:
            #         logger.warning(f"URL не найден (404): {url}")
            #         return
            #     raise requests.HTTPError(
            #         f"Статус: {response.status_code} для URL: {url}",
            #         response=response,
            #     )
            # if response.status_code == 429:
            #     retry_after = int(response.headers.get("Retry-After", 60))
            #     sys.exit(1)

            if response.status_code == 200 and "text/html" in response.headers.get(
                "Content-Type", ""
            ):
                file_path.write_text(response.text, encoding="utf-8")

                with fetch_lock:
                    successful_urls.add(url)

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
