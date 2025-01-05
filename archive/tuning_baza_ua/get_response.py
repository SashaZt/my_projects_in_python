import hashlib
import random
import sys
import threading
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
import urllib3
from configuration.logger_setup import logger
from tenacity import wait_exponential  # Используем экспоненциальную задержку
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)
from tqdm import tqdm
from working_with_files import Working_with_files

# Отключаем предупреждение InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GetResponse:
    """Класс для работы с HTTP-запросами, загрузки HTML и изображений с использованием многопоточности и прокси."""

    def __init__(
        self,
        max_workers,
        cookies,
        headers,
        html_files_directory,
        file_proxy,
        url_sitemap,
        json_result,
        output_csv_file,
        img_files_directory,
    ) -> None:
        self.max_workers = max_workers
        self.cookies = cookies
        self.headers = headers
        self.html_files_directory = html_files_directory
        self.img_files_directory = img_files_directory
        self.file_proxy = file_proxy
        self.json_result = json_result
        self.output_csv_file = output_csv_file
        self.url_sitemap = url_sitemap
        self.stop_event = threading.Event()
        self.working_files = Working_with_files(file_proxy, json_result)
        self.proxies = self.working_files.load_proxies()  # Загружаем прокси
        self.failed_proxies = {}  # Для хранения прокси и числа неудачных попыток
        """Инициализирует класс с настройками для работы с HTTP-запросами и загрузками.

        Args:
            max_workers (int): Максимальное количество потоков для многопоточности.
            cookies (dict): Куки для запросов.
            headers (dict): Заголовки для запросов.
            html_files_directory (Path): Директория для сохранения HTML файлов.
            file_proxy (Path): Путь к файлу с прокси-серверами.
            url_sitemap (str): URL для загрузки sitemap.
            json_result (Path): Путь к JSON файлу для сохранения результатов.
            output_csv_file (Path): Путь к CSV файлу для сохранения URL.
            img_files_directory (Path): Директория для сохранения изображений.
        """
        # Инициализация атрибутов класса

    def _choose_proxy(self):
        """Выбирает случайный доступный прокси, исключая заблокированные или многократно неудачные.

        Returns:
            dict: Словарь с прокси для использования в запросе или пустой словарь для прямого соединения.
        """
        available_proxies = [
            p for p in self.proxies if self.failed_proxies.get(p, 0) < 3]

        if not available_proxies:
            # logger.warning(
            #     "Нет доступных прокси. Используем прямое соединение.")
            return {}

        proxy = random.choice(available_proxies)
        return {"http": proxy, "https": proxy}

    def mark_failed_proxy(self, proxy):
        """Отмечает прокси как неудачный и увеличивает счетчик ошибок для исключения из списка.

        Args:
            proxy (str): Прокси-сервер, который был использован в неудачном запросе.
        """
        if proxy:
            self.failed_proxies[proxy] = self.failed_proxies.get(proxy, 0) + 1
            if self.failed_proxies[proxy] >= 3:
                logger.warning(
                    f"Прокси {proxy} будет исключен после 3 неудачных попыток.")

    def fetch_xml(self, url):
        """Загружает XML файл по указанному URL.

        Args:
            url (str): URL для загрузки XML.

        Returns:
            bytes or None: Содержимое XML файла в байтах или None, если запрос не удался.
        """
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
                logger.error(f"Ошибка при скачивании файла: {
                             response.status_code} для URL: {url}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе URL {url}: {e}")
            return None

    def get_sitemap_start(self):
        """Начинает загрузку sitemap из URL, указанного в инициализации.

        Returns:
            bytes or None: Содержимое XML sitemap или None, если загрузка не удалась.
        """
        return self.fetch_xml(self.url_sitemap)

    def parsing_sitemap_start(self):
        """Парсит и обрабатывает основной sitemap для получения списка URL продуктов.

        Returns:
            list: Список URL продуктов.
        """
        content = self.get_sitemap_start()
        if content:
            return self.parsing_sitemap(content)
        return []

    def parsing_sitemap(self, content):
        """Извлекает URL продуктов из XML sitemap и сохраняет их в CSV.

        Args:
            content (bytes): Содержимое XML файла.

        Returns:
            None
        """
        root = ET.fromstring(content)
        # Определение пространства имен
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Извлечение всех тегов <loc> и исключение ссылок, содержащих "https://protune.com.ua/image/"
        locations = root.findall(".//ns:loc", namespace)
        urls = [
            loc.text.strip() for loc in locations if loc.text
            #  and "https://protune.com.ua/image/" not in loc.text
        ]
        logger.info("Получили список всех sitemap")
        self.working_files.save_urls_to_csv(urls, self.output_csv_file)
        return

    def process_infox_file(self):
        """Проходит по списку URL из CSV файла и скачивает HTML страницы.

        Returns:
            None
        """
        urls_df = pd.read_csv(self.output_csv_file)
        total_urls = len(urls_df)
        progress_bar = tqdm(total=total_urls, desc="Обработка файлов")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for url in urls_df["url"]:
                hash_object = hashlib.sha256(url.encode())
                identifier = hash_object.hexdigest()
                file_path = self.html_files_directory / f"{identifier}.html"

                if file_path.exists():
                    progress_bar.update(1)
                    continue

                futures.append(executor.submit(
                    self.fetch_and_save_html, url, file_path))

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error occurred: {e}")
                finally:
                    progress_bar.update(1)

        progress_bar.close()

    @retry(
        stop=stop_after_attempt(5),
        # Экспоненциальная задержка с ростом до 30 секунд
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type(requests.RequestException)
    )
    def fetch_and_save_html(self, url, file_path):
        """Загружает HTML страницу по URL и сохраняет ее в файл с применением прокси и задержек при неудаче.

        Args:
            url (str): URL для загрузки HTML страницы.
            file_path (Path): Путь для сохранения HTML страницы.

        Returns:
            None
        """
        if self.stop_event.is_set():
            return

        proxy_dict = self._choose_proxy()  # Выбираем прокси или работаем без него
        proxy = proxy_dict.get("http", None)

        try:
            response = requests.get(
                url,
                headers=self.headers,
                proxies=proxy_dict,
                timeout=30,
                cookies=self.cookies,
                verify=False
            )

            if response.status_code >= 400:
                if response.status_code == 404:
                    logger.warning(f"URL не найден (404): {url}")
                    return
                raise requests.HTTPError(f"Статус: {response.status_code} для URL: {
                                         url}", response=response)

            if response.status_code == 200 and "text/html" in response.headers.get("Content-Type", ""):
                file_path.write_text(response.text, encoding="utf-8")
            else:
                logger.error(f"Некорректный тип содержимого для URL: {url}")
                raise requests.HTTPError(f"Некорректный тип содержимого для URL: {
                                         url}", response=response)

        except requests.RequestException as e:
            logger.error(f"Ошибка при обработке запроса для URL {url}: {e}")
            self.mark_failed_proxy(proxy)  # Отмечаем прокси как неудачный
            raise  # Повторяем запрос после задержки
        except Exception as e:
            logger.error(f"Произошла ошибка при обработке {url}: {e}")

    def process_infox_img(self):
        """Загружает изображения продуктов, указанных в JSON результатах, и сохраняет их в директорию изображений.

        Returns:
            None
        """
        json_datas = self.working_files.read_json_result()
        tasks = []
        total_urls = len(json_datas)

        # Создаем директорию, если ее нет
        progress_bar = tqdm(total=total_urls, desc="Обработка файлов")

        # Многопоточность для загрузки изображений
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for json_data in json_datas:
                name_file = json_data["model"]
                url_file = json_data["image_url"]
                file_path = self.img_files_directory / f"{name_file}.jpeg"
                if file_path.exists():
                    progress_bar.update(1)
                    continue
                # Отправляем задачу на выполнение
                tasks.append(executor.submit(
                    self.download_image, url_file, file_path))

            # Обрабатываем задачи по мере завершения
            for future in as_completed(tasks):
                result = future.result()
                if result:
                    progress_bar.update(1)

        progress_bar.close()

    @retry(stop=stop_after_attempt(10), wait=wait_fixed(30), retry=retry_if_exception_type(requests.RequestException))
    def download_image(self, url, file_path):
        """Скачивает изображение по указанному URL и сохраняет его в файл с использованием прокси.

        Args:
            url (str): URL изображения.
            file_path (Path): Путь для сохранения изображения.

        Returns:
            Path or None: Путь к сохраненному изображению или None при ошибке.
        """
        try:
            proxies_dict = self._choose_proxy()
            response = requests.get(
                url, headers=self.headers, proxies=proxies_dict, cookies=self.cookies, stream=True)
            response.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return file_path
        except Exception as e:
            print(f"Не удалось загрузить {url}. Ошибка: {e}")
            return None
