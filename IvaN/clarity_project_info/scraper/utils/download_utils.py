# /utils/download_utils.py
import asyncio
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import aiofiles
import requests
from bs4 import BeautifulSoup
from config.constants import COOKIES, HEADERS
from config.logger import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
from utils.proxy_utils import get_random_proxy

from config.config import MAX_WORKERS, RETRY_ATTEMPTS, RETRY_DELAY


class DownloadProgress:
    """Класс для отслеживания прогресса скачивания."""

    def __init__(self, total_items: int):
        self.total_items = total_items
        self.downloaded_items = 0
        self.failed_items = 0
        self.lock = threading.Lock()
        self.async_lock = asyncio.Lock()

    def update(self, success: bool):
        """Обновляет статус скачивания (синхронная версия)."""
        with self.lock:
            if success:
                self.downloaded_items += 1
            else:
                self.failed_items += 1
            self._print_progress()

    async def async_update(self, success: bool):
        """Обновляет статус скачивания (асинхронная версия)."""
        async with self.async_lock:
            if success:
                self.downloaded_items += 1
            else:
                self.failed_items += 1
            self._print_progress()

    def _print_progress(self):
        """Выводит прогресс в консоль."""
        completed = self.downloaded_items + self.failed_items
        percentage = (completed / self.total_items) * 100
        logger.info(
            f"Прогресс: {completed}/{self.total_items} ({percentage:.1f}%) | "
            f"Успешно: {self.downloaded_items} | Ошибки: {self.failed_items}"
        )


@retry(
    stop=stop_after_attempt(RETRY_ATTEMPTS),
    wait=wait_fixed(RETRY_DELAY),
    retry=retry_if_exception_type(requests.RequestException),
)
def download_file(url: str, output_path: Path, proxies: List[str]) -> bool:
    """Скачивает файл по указанному URL без использования сессии."""
    proxy_dict = get_random_proxy(proxies)

    # Добавляем уникальный параметр к URL для предотвращения кэширования
    random_param = f"{'&' if '?' in url else '?'}nocache={random.randint(1, 1000000)}"
    request_url = f"{url}{random_param}"

    try:
        response = requests.get(
            request_url,
            cookies=COOKIES,
            headers=HEADERS,
            timeout=30,
            proxies=proxy_dict,
        )

        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            logger.info(f"Скачали файл {url}")
            return True
        else:
            logger.error(f"Ошибка {response.status_code} при загрузке {url}")
            return False
    except requests.RequestException as e:
        logger.error(f"Ошибка при обработке запроса для URL {url}: {e}")
        raise


def download_gz_files(
    links: List[str], output_dir: Path, proxies: List[str], max_workers: int
) -> None:
    """Скачивает архивы в многопоточном режиме с отслеживанием прогресса."""
    output_dir.mkdir(parents=True, exist_ok=True)
    progress = DownloadProgress(len(links))

    def download_link(link: str) -> None:
        file_name = output_dir / Path(urlparse(link).path).name
        if not file_name.exists():
            try:
                success = download_file(link, file_name, proxies)
                progress.update(success)
            except Exception as e:
                logger.error(f"Ошибка при скачивании {link}: {e}")
                progress.update(False)
        else:
            logger.info(f"Файл {file_name} уже существует, пропуск.")
            progress.update(True)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(download_link, links)


async def download_html_direct(url: str, proxies: List[str]) -> Optional[str]:
    """Асинхронно скачивает HTML напрямую через requests."""
    # Получаем прокси для этого запроса
    proxy_dict = get_random_proxy(proxies)

    # Добавляем уникальный параметр к URL для предотвращения кэширования
    random_param = f"{'&' if '?' in url else '?'}nocache={random.randint(1, 1000000)}"
    request_url = f"{url}{random_param}"

    try:
        # Запускаем в отдельном потоке, чтобы не блокировать асинхронный цикл
        def fetch():
            try:
                response = requests.get(
                    request_url,
                    headers=HEADERS,
                    cookies=COOKIES,
                    timeout=30,
                    proxies=proxy_dict,
                )
                if response.status_code == 200:
                    return response.text
                else:
                    return None
            except Exception as e:
                logger.error(f"Ошибка в fetch для URL {request_url}: {e}")
                return None

        # Запускаем синхронную функцию в отдельном потоке
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(None, fetch)

        if content:
            soup = BeautifulSoup(content, "lxml")
            h1_element = soup.find("h1")

            if h1_element and h1_element.text.strip() == "Шановний користувачу!":
                logger.info(
                    f"Пропуск сохранения для URL {url}: "
                    f"обнаружен текст 'Шановний користувачу!'"
                )
                return None
            return content
        else:
            logger.error(f"Ошибка при получении HTML для URL {url}")
            return None
    except Exception as e:
        logger.error(f"Ошибка запроса для URL {url}: {e}")
        return None


async def save_html_file(html_content: str, output_dir: Path, url: str) -> None:
    """Асинхронно сохраняет HTML содержимое в файл."""
    filename = output_dir / f"{urlparse(url).path.replace('/', '_')}.html"
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(html_content)
    logger.info(f"HTML файл сохранен: {filename}")


async def async_download_html_with_proxies(
    urls: List[str], proxies: List[str], output_dir: Path, max_workers: int
) -> None:
    """Асинхронная пакетная загрузка HTML с очередью и отслеживанием прогресса."""
    # Создаём очередь URL для обработки
    queue = asyncio.Queue()
    for url in urls:
        await queue.put(url)

    progress = DownloadProgress(len(urls))

    async def worker() -> None:
        while not queue.empty():
            url = await queue.get()

            # Здесь мы не проверяем существование файла,
            # так как теперь список URL уже предварительно отфильтрован
            html_content = await download_html_direct(url, proxies)

            if html_content:
                await save_html_file(html_content, output_dir, url)
                await progress.async_update(True)
            else:
                await progress.async_update(False)

            queue.task_done()

    tasks = [worker() for _ in range(max_workers)]
    await asyncio.gather(*tasks)
