import asyncio
from base64 import b64decode
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import aiofiles
import pandas as pd  # Импортируем pandas
from bs4 import BeautifulSoup  # Импорт BeautifulSoup
from configuration.logger_setup import logger
from dotenv import load_dotenv
from zyte_api import AsyncZyteAPI  # Импорт клиента Zyte API

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

html_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

# Загрузка переменных окружения из файла .env
load_dotenv(Path("configuration") / ".env")
csv_all_edrs_products = data_directory / "urls.csv"

# Загрузка списка URL из CSV файла


def load_urls(file_path: Path) -> List[str]:
    """Загружает список URL из CSV файла."""
    df = pd.read_csv(file_path)
    if "url" not in df.columns:
        raise ValueError("CSV файл должен содержать колонку 'url'.")
    return df["url"].tolist()


# Асинхронная функция для сохранения HTML содержимого в файл


async def save_html_file(html_content: str, output_dir: Path, url: str) -> None:
    """Асинхронно сохраняет HTML содержимое в файл, используя URL в качестве имени файла."""
    filename = output_dir / f"{urlparse(url).path.replace('/', '_')}.html"
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(html_content)
    logger.info(f"HTML файл сохранен: {filename}")


# Асинхронная функция для скачивания HTML с использованием Zyte API клиента


async def download_html(client: AsyncZyteAPI, url: str) -> Optional[str]:
    """Асинхронно скачивает HTML по заданному URL с использованием клиента Zyte API."""
    try:
        # Выполняем запрос к Zyte API
        api_response = await client.get(
            {
                "url": url,
                "httpResponseBody": True,
            }
        )
        # Декодируем содержимое HTTP тела ответа из base64
        content = b64decode(api_response["httpResponseBody"]).decode("utf-8")

        # Используем BeautifulSoup для проверки содержимого
        soup = BeautifulSoup(content, "html.parser")
        h1_element = soup.find("h1")
        # Проверяем наличие <h1> с текстом "Шановний користувачу!"
        if h1_element and h1_element.text.strip() == "Шановний користувачу!":
            logger.info(
                f"Пропуск сохранения для URL {
                        url}: обнаружен текст 'Шановний користувачу!'"
            )
            return None  # Пропускаем, если обнаружен данный текст
        return content
    except Exception as e:
        logger.error(f"Ошибка запроса для URL {url}: {e}")
        return None


# Асинхронная функция для пакетной загрузки HTML с очередью


async def async_download_html_with_proxies(
    urls: List[str], html_files_directory: Path, max_workers: int
) -> None:
    async with AsyncZyteAPI(api_key="45a471f3c80945659831851313028a78") as client:
        # Создаем очередь URL для обработки
        queue = asyncio.Queue()
        for url in urls:
            await queue.put(url)

        async def worker() -> None:
            while not queue.empty():
                url = await queue.get()
                name_file = url.split("/")[-1].replace("-", "_")
                html_company = html_files_directory / f"{name_file}.html"
                if html_company.exists():
                    queue.task_done()
                    continue

                try:
                    html_content = await download_html(client, url)
                    if html_content:
                        await save_html_file(html_content, html_files_directory, url)
                except Exception as e:
                    logger.error(f"Ошибка при обработке URL {url}: {e}")
                finally:
                    queue.task_done()

        tasks = [worker() for _ in range(max_workers)]
        await asyncio.gather(*tasks)


# Основная функция для запуска асинхронного процесса


async def main():
    urls = load_urls(csv_all_edrs_products)
    max_workers = 1  # Указание количества потоков
    await async_download_html_with_proxies(urls, html_files_directory, max_workers)


# Запуск основной асинхронной функции
if __name__ == "__main__":
    asyncio.run(main())
