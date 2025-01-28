import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from tqdm import tqdm

current_directory = Path.cwd()
data_directory = current_directory / "data"
html_directory = current_directory / "html"
configuration_directory = current_directory / "configuration"
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)

proxy_file_txt = configuration_directory / "proxies.txt"


class DataDownloader:
    def __init__(
        self,
        base_url: str = None,
        output_dir: str = "downloads",
        max_workers: int = 5,
        timeout: int = 30,
        delay: int = 0,
        cookies: Dict = None,
        headers: Dict = None,
        proxy_file: str = None,
    ):
        """
        Инициализация загрузчика данных.

        :param base_url: Базовый URL для скачивания
        :param output_dir: Директория для сохранения файлов
        :param max_workers: Максимальное количество потоков
        :param timeout: Таймаут для запросов
        :param delay: Задержка между запросами в секундах
        :param cookies: Куки для запросов
        :param headers: Заголовки для запросов
        :param proxy_file: Путь к файлу со списком прокси
        """
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.timeout = timeout
        self.delay = delay
        self.cookies = cookies or {}
        self.headers = headers or {}
        self.proxies = self.load_proxies(proxy_file) if proxy_file else []

        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        # Создание директории для сохранения
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_proxies(self, proxy_file: str) -> List[str]:
        """
        Загрузка списка прокси из файла.

        :param proxy_file: Путь к файлу с прокси
        :return: Список прокси
        """
        try:
            with open(proxy_file, "r", encoding="utf-8") as file:
                proxies = [line.strip() for line in file if line.strip()]
            self.logger.info(f"Загружено {len(proxies)} прокси")
            return proxies
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке прокси: {str(e)}")
            return []

    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """
        Получение случайного прокси из списка.

        :return: Словарь с настройками прокси или None
        """
        if not self.proxies:
            return None

        proxy = random.choice(self.proxies)
        return {"http": proxy, "https": proxy}

    def build_url(self, url: str) -> str:
        """Построение полного URL"""
        if self.base_url and not url.startswith(("http://", "https://")):
            return f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
        return url

    def download_file(self, url: str, file_extension: str = "html") -> Optional[str]:
        """
        Скачивание одного файла.

        :param url: URL для скачивания
        :param file_extension: Расширение для сохраняемого файла
        :return: Содержимое ответа или None в случае ошибки
        """
        full_url = self.build_url(url)
        file_path = self.output_dir / f"{url}.{file_extension}"

        # Пропускаем, если файл уже существует
        if file_path.exists():
            self.logger.debug(f"Файл {file_path} уже существует")
            return None

        try:
            # Получаем случайный прокси
            proxies = self.get_random_proxy()

            # Формируем параметры запроса
            request_params = {
                "url": full_url,
                "cookies": self.cookies,
                "headers": self.headers,
                "timeout": self.timeout,
            }

            # Добавляем прокси если есть
            if proxies:
                request_params["proxies"] = proxies
                self.logger.debug(f"Используется прокси: {proxies}")

            response = requests.get(**request_params)
            response.raise_for_status()

            # Сохранение файла
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            if self.delay:
                time.sleep(self.delay)

            return response.text

        except Exception as e:
            self.logger.error(f"Ошибка при скачивании {full_url}: {str(e)}")
            return None

    def download_batch(
        self, urls: List[str], file_extension: str = "html", show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Пакетное скачивание файлов.

        :param urls: Список URL для скачивания
        :param file_extension: Расширение для сохраняемых файлов
        :param show_progress: Показывать ли прогресс-бар
        :return: Словарь с результатами {url: content}
        """
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.download_file, url, file_extension): url
                for url in urls
            }

            futures = list(future_to_url.keys())
            if show_progress:
                futures = tqdm(futures, total=len(urls), desc="Скачивание")

            for future in as_completed(futures):
                url = future_to_url[future]
                try:
                    content = future.result()
                    if content:
                        results[url] = content
                except Exception as e:
                    self.logger.error(f"Ошибка при обработке {url}: {str(e)}")

        return results


def main():
    # Пример использования
    cookies = {"your_cookie": "value"}

    headers = {"User-Agent": "Mozilla/5.0 ..."}

    # Создаем экземпляр загрузчика
    downloader = DataDownloader(
        base_url="https://edrpou.ubki.ua/ua",
        output_dir=data_directory,
        max_workers=5,
        delay=5,
        cookies=cookies,
        headers=headers,
        proxy_file=proxy_file_txt,  # Путь к файлу с прокси
    )

    # Читаем URLs из CSV
    urls_df = pd.read_csv("urls.csv")
    urls = urls_df["url"].tolist()

    # Запускаем скачивание
    results = downloader.download_batch(urls, file_extension="html", show_progress=True)

    # Выводим статистику
    print(f"Успешно скачано: {len(results)} из {len(urls)} файлов")


if __name__ == "__main__":
    main()

"""
# Без прокси (локальная работа)
downloader = DataDownloader(max_workers=3)

# С прокси
downloader = DataDownloader(
    max_workers=3,
    proxy_file="proxies.txt"
)

# Полная настройка
downloader = DataDownloader(
    base_url='https://example.com',
    output_dir='downloads',
    max_workers=10,
    timeout=60,
    delay=2,
    cookies={'session': 'value'},
    headers={'User-Agent': 'Custom Agent'},
    proxy_file='proxies.txt'
)
"""
