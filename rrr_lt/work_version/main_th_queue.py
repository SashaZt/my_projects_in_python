import asyncio
import sys
import threading
import time
import urllib.parse
from pathlib import Path
from queue import Empty, Queue
from typing import Dict, Optional

import requests
from database import create_database, extract_and_save_codes
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


class ThreadedScraperCode:
    def __init__(
        self,
        num_threads: int,
        api_key: str,
        html_code_directory: Path,
        max_retries: int = 95,
        delay: int = 30,
    ):
        self.num_threads = num_threads
        self.api_key = api_key
        self.html_code_directory = html_code_directory
        self.max_retries = max_retries
        self.delay = delay

        # Инициализация очереди
        self.task_queue = Queue()
        self.active_threads = []
        self.stop_event = threading.Event()

        # Счетчик обработанных задач
        self.processed_count = 0
        self.processed_lock = threading.Lock()

        # Прогресс-бар
        self.total_tasks = 0
        self.progress_bar = None

        # Заголовки запроса
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en;q=0.9,uk;q=0.8",
            "x-requested-with": "XMLHttpRequest",
        }
        asyncio.run(create_database())

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

    def process_page(self, page: int) -> None:
        """Обрабатывает одну страницу"""
        # logger.info(f"Обработка страницы {page}")
        try:
            html_file = self.html_code_directory / f"page_{page}.html"
            if html_file.exists():
                with self.processed_lock:
                    self.processed_count += 1
                    if self.progress_bar:
                        self.progress_bar.update(1)
                return
            # Параметры для ScraperAPI
            payload = {
                "api_key": self.api_key,
                "keep_headers": "true",  # Важно для сохранения пользовательских заголовков
                # 'render': 'true'  # Включаем рендеринг JavaScript
            }
            # Формируем URL и параметры
            if page == 0:
                url = "https://rrr.lt/ru/spisok-kodov-zapasnykh-chastey"
                payload["url"] = f"{url}"
            else:
                url = f"https://rrr.lt/ru/spisok-kodov-zapasnykh-chastey?page={page}"
                params = {
                    "page": page,
                }
                # Добавляем параметры запроса к URL
                payload["url"] = f"{url}?{urllib.parse.urlencode(params)}"

            response = self.make_request_with_retries(
                "https://api.scraperapi.com/", payload, headers=self.headers
            )

            if response:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(extract_and_save_codes(response.text))
                loop.close()
                with open(html_file, "w", encoding="utf-8") as file:
                    file.write(response.text)

                with self.processed_lock:
                    self.processed_count += 1
                    if self.progress_bar:
                        self.progress_bar.update(1)
            else:
                logger.error(f"Не удалось загрузить страницу {page}")

        except Exception as e:
            logger.error(f"Ошибка при обработке страницы {page}: {e}")

    def worker(self) -> None:
        """Рабочий поток, обрабатывающий задачи из очереди"""
        while not self.stop_event.is_set():
            try:
                page = self.task_queue.get(timeout=1)
                try:
                    self.process_page(page)
                finally:
                    self.task_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Ошибка в потоке {threading.current_thread().name}: {e}")
                time.sleep(1)

    def start(self) -> None:
        """Запускает пул рабочих потоков"""
        self.stop_event.clear()
        self.processed_count = 0

        for _ in range(self.num_threads):
            thread = threading.Thread(target=self.worker, daemon=True)
            thread.start()
            self.active_threads.append(thread)

    def stop(self) -> None:
        """Останавливает все рабочие потоки"""
        self.stop_event.set()

        for thread in self.active_threads:
            thread.join()

        self.active_threads.clear()
        if self.progress_bar:
            self.progress_bar.close()

    def add_pages(self, total_pages: int) -> None:
        """Добавляет страницы в очередь для обработки"""
        self.total_tasks = total_pages + 1  # +1 для страницы 0
        self.progress_bar = tqdm(
            total=self.total_tasks,
            desc="Обработка страниц",
            bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
        )
        for page in range(total_pages + 1):
            self.task_queue.put(page)

    def wait_completion(self) -> None:
        """Ожидает завершения всех задач в очереди"""
        self.task_queue.join()

    @property
    def tasks_processed(self) -> int:
        """Возвращает количество обработанных задач"""
        return self.processed_count


def process_pages_with_threads_code(
    total_pages: int, num_threads: int = 95, **kwargs
) -> None:
    """
    Обрабатывает страницы с использованием пула потоков

    Args:
        total_pages: Количество страниц для обработки
        num_threads: Количество рабочих потоков
        **kwargs: Дополнительные параметры для ThreadedScraperCode
    """
    scraper = ThreadedScraperCode(num_threads=num_threads, **kwargs)

    try:
        scraper.start()
        scraper.add_pages(total_pages)
        scraper.wait_completion()
    finally:
        scraper.stop()
