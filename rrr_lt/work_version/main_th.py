import asyncio
import sys
import threading
import time
import urllib.parse
from pathlib import Path
from queue import Empty, Queue
from typing import Dict, List, Optional

import requests
from database import (
    create_database,
    extract_and_save_product,
    get_all_codes,
    get_all_codes_products,
)
from loguru import logger
from tqdm import tqdm

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
        max_retries: int = 95,
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
        # Прогресс-бар
        self.total_tasks = 0
        self.progress_bar = None

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
        # Создаем БД при инициализации
        asyncio.run(create_database())
        codes_data = asyncio.run(get_all_codes_products())
        # Создаем множества для быстрого поиска
        self.existing_search_queries = set(row[0] for row in codes_data if row[0])
        self.existing_codes = set(row[1] for row in codes_data if row[1])

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
            # json_file = self.json_product_directory / f"{id_product}.json"
            # if json_file.exists():
            #     with self.processed_lock:
            #         self.processed_count += 1
            #         if self.progress_bar:
            #             self.progress_bar.update(1)
            #     return
            # Проверяем наличие code в базе данных вместо файла
            if (
                id_product in self.existing_search_queries
                or id_product in self.existing_codes
            ):
                # logger.info(f"Продукт {id_product} уже обработан")
                with self.processed_lock:
                    self.processed_count += 1
                    if self.progress_bar:
                        self.progress_bar.update(1)
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
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    extract_and_save_product(response.text, id_product)
                )
                loop.close()
                # if response:
                #     with open(json_file, "w", encoding="utf-8") as file:
                #         file.write(response.text)
                #     loop = asyncio.new_event_loop()
                #     asyncio.set_event_loop(loop)
                #     loop.run_until_complete(
                #         extract_and_save_product(response.text, json_file)
                #     )
                #     loop.close()
                # Добавляем новый код в список существующих
                self.existing_codes.add(id_product)

                with self.processed_lock:
                    self.processed_count += 1
                    if self.progress_bar:
                        self.progress_bar.update(1)
            else:
                logger.error(f"Не удалось загрузить данные для продукта {id_product}")

        except Exception as e:
            logger.error(f"Ошибка при обработке продукта {id_product}: {e}")

    def worker(self) -> None:
        """Рабочий поток, обрабатывающий задачи из очереди"""
        thread_name = threading.current_thread().name
        # logger.debug(f"Запущен поток {thread_name}")

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

        # logger.debug(f"Поток {thread_name} завершил работу")

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

        for thread in self.active_threads:
            thread.join()

        self.active_threads.clear()
        if self.progress_bar:
            self.progress_bar.close()

    def add_task(self, id_product: str) -> None:
        """Добавляет задачу в очередь"""
        self.task_queue.put(id_product)

    def add_tasks(self, id_products: List[str]) -> None:
        """Добавляет список задач в очередь"""
        self.total_tasks = len(id_products)
        self.progress_bar = tqdm(
            total=self.total_tasks,
            desc="Обработка файлов",
            bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
        )
        for id_product in id_products:
            self.task_queue.put(id_product)

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
    id_products: List[str], num_threads: int = 95, **kwargs
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
