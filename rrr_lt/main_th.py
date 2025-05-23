import json
import sys
import threading
import time
import urllib.parse
from pathlib import Path
from queue import Empty, Queue
from typing import Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from config import COOKIES, HEADERS
from loguru import logger

# API_KEY = "6c54502fd688c7ce737f1c650444884a"
API_KEY = "b7141d2b54426945a9f0bf6ab4c7bc54"
# Настройте максимальное количество попыток, если требуется
MAX_RETRIES = 10
RETRY_DELAY = 30  # Задержка между попытками в секундах


current_directory = Path.cwd()
html_code_directory = current_directory / "html_code"
json_product_directory = current_directory / "json_product"
log_directory = current_directory / "log"
data_directory = current_directory / "data"
log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
json_product_directory.mkdir(parents=True, exist_ok=True)
html_code_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
xlsx_result = data_directory / "result.xlsx"
output_csv_file = data_directory / "output.csv"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


class ThreadedScraper:
    def __init__(
        self,
        num_threads: int,
        api_key: str,
        base_url: str,
        headers: Dict,
        cookies: Dict,
        json_product_directory: Path,
        max_retries: int = 10,
        delay: int = 30,
    ):
        self.num_threads = num_threads
        self.api_key = api_key
        self.base_url = base_url
        self.headers = headers.copy()
        self.cookies = cookies
        self.json_product_directory = json_product_directory
        self.max_retries = max_retries
        self.delay = delay

        # Инициализация очереди
        self.task_queue = Queue()
        self.active_threads = []
        self.stop_event = threading.Event()

        # Счетчик обработанных задач
        self.processed_count = 0
        self.processed_lock = threading.Lock()

        # Формируем строку Cookie из словаря cookies
        cookie_string = "; ".join(f"{key}={value}" for key, value in cookies.items())
        self.headers["Cookie"] = cookie_string

    def make_request_with_retries(
        self, url: str, params: Dict, headers: Optional[Dict] = None
    ) -> Optional[requests.Response]:
        """Выполняет запрос с повторными попытками"""
        retries = 0
        while retries < self.max_retries and not self.stop_event.is_set():
            try:
                response = requests.get(url, params=params, headers=headers, timeout=60)
                if response.status_code == 200:
                    return response
                else:
                    logger.warning(
                        f"Ошибка {response.status_code} при запросе {url}. "
                        f"Попытка {retries + 1}/{self.max_retries}."
                    )
            except Exception as e:
                logger.error(
                    f"Ошибка при выполнении запроса: {e}. "
                    f"Попытка {retries + 1}/{self.max_retries}."
                )
            retries += 1
            if not self.stop_event.is_set():
                time.sleep(self.delay)

        logger.error(
            f"Не удалось выполнить запрос после {self.max_retries} попыток: {url}"
        )
        return None

    def process_product(self, id_product: str) -> None:
        """Обрабатывает один продукт"""
        try:
            json_file = self.json_product_directory / f"{id_product}.json"
            if json_file.exists():
                logger.info(f"Файл {json_file} уже существует. Пропускаем.")
                return

            # Формируем параметры запроса
            query_params = {"q": id_product, "prs": "2", "page": "1"}
            full_url = f"{self.base_url}?{urllib.parse.urlencode(query_params)}"

            # Параметры для ScraperAPI
            payload = {
                "api_key": self.api_key,
                "url": full_url,
                "keep_headers": "true",
            }

            response = self.make_request_with_retries(
                "https://api.scraperapi.com/", payload, headers=self.headers
            )

            if response:
                with open(json_file, "w", encoding="utf-8") as file:
                    file.write(response.text)
                logger.info(f"Скачано {json_file}")

                # Увеличиваем счетчик обработанных задач
                with self.processed_lock:
                    self.processed_count += 1
            else:
                logger.error(f"Не удалось загрузить данные для продукта {id_product}")

        except Exception as e:
            logger.error(f"Ошибка при обработке продукта {id_product}: {e}")

    def worker(self) -> None:
        """Рабочий поток, обрабатывающий задачи из очереди"""
        thread_name = threading.current_thread().name
        logger.debug(f"Запущен поток {thread_name}")

        while not self.stop_event.is_set():
            try:
                # Получаем задачу из очереди с таймаутом
                try:
                    id_product = self.task_queue.get(timeout=1)
                except Empty:
                    continue

                try:
                    self.process_product(id_product)
                except Exception as e:
                    logger.error(
                        f"Ошибка при обработке продукта в потоке {thread_name}: {e}"
                    )
                finally:
                    self.task_queue.task_done()

            except Exception as e:
                logger.error(f"Критическая ошибка в потоке {thread_name}: {e}")
                if not self.stop_event.is_set():
                    time.sleep(1)  # Пауза перед следующей попыткой

        logger.debug(f"Поток {thread_name} завершил работу")

    def start(self) -> None:
        """Запускает пул рабочих потоков"""
        self.stop_event.clear()
        self.processed_count = 0

        # Создаем и запускаем потоки
        for _ in range(self.num_threads):
            thread = threading.Thread(target=self.worker, daemon=True)
            thread.start()
            self.active_threads.append(thread)

        logger.info(f"Запущено {self.num_threads} рабочих потоков")

    def stop(self) -> None:
        """Останавливает все рабочие потоки"""
        self.stop_event.set()

        # Ждем завершения всех потоков
        for thread in self.active_threads:
            thread.join()

        self.active_threads.clear()
        logger.info("Все рабочие потоки остановлены")

    def add_task(self, id_product: str) -> None:
        """Добавляет задачу в очередь"""
        self.task_queue.put(id_product)

    def add_tasks(self, id_products: List[str]) -> None:
        """Добавляет список задач в очередь"""
        for id_product in id_products:
            self.add_task(id_product)

    def wait_completion(self) -> None:
        """Ожидает завершения всех задач в очереди"""
        self.task_queue.join()

    @property
    def tasks_processed(self) -> int:
        """Возвращает количество обработанных задач"""
        return self.processed_count

    @property
    def queue_size(self) -> int:
        """Возвращает текущий размер очереди"""
        return self.task_queue.qsize()


# Пример использования:
def process_products_with_threads(
    id_products: List[str], num_threads: int = 10, **kwargs
) -> None:
    """
    Обрабатывает список продуктов с использованием пула потоков

    Args:
        id_products: Список ID продуктов для обработки
        num_threads: Количество рабочих потоков
        **kwargs: Дополнительные параметры для ThreadedScraper
    """
    scraper = ThreadedScraper(num_threads=num_threads, **kwargs)

    try:
        # Запускаем рабочие потоки
        scraper.start()

        # Добавляем задачи в очередь
        scraper.add_tasks(id_products)

        # Ждем завершения всех задач
        scraper.wait_completion()

        logger.info(f"Обработано продуктов: {scraper.tasks_processed}")

    finally:
        # Останавливаем потоки
        scraper.stop()


id_products = [
    "5802243444",
    "7355163422",
]  # Список ID продуктов
process_products_with_threads(
    id_products=id_products,
    num_threads=10,
    api_key=API_KEY,
    base_url="https://rrr.lt/ru/poisk",
    headers=HEADERS,
    cookies=COOKIES,
    json_product_directory=json_product_directory,
    max_retries=MAX_RETRIES,
    delay=RETRY_DELAY,
)
