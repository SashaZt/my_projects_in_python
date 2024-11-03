import asyncio
import gzip
import os
import random
import shutil
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import aiofiles
import aiohttp
import pandas as pd  # Импортируем pandas
import requests
from bs4 import BeautifulSoup  # Импорт BeautifulSoup
from configuration.logger_setup import logger
from dotenv import load_dotenv
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)

# Установка директорий для логов и данных
current_directory = Path.cwd()
gz_directory = current_directory / "gz"
xml_directory = current_directory / "xml"
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

gz_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

# Загрузка переменных окружения из файла .env
load_dotenv(Path("configuration") / ".env")
xml_sitemap = data_directory / "sitemap_index.xml"
csv_url_site_maps = data_directory / "url_site_maps.csv"
output_csv_file = data_directory / "output.csv"
csv_all_urls_products = data_directory / "all_urls.csv"
csv_all_edrs_products = data_directory / "all_edrs.csv"

csv_file_successful = data_directory / "identifier_successful.csv"
xlsx_result = data_directory / "result.xlsx"
file_proxy = configuration_directory / "roman.txt"

cookies = {
    'PHPSESSID': 'c95e174e4800458653c20b9dc207596e',
    'stats-mode': '',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en;q=0.9,uk;q=0.8',
    'cache-control': 'no-cache',
    'dnt': '1',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
}

# 1. Скачать основной файл sitemap-index.xml
SITEMAP_INDEX_URL = os.getenv("SITEMAP_INDEX_URL")
# 2. Парсинг sitemap-index.xml и запись в CSV файл


def load_proxies() -> List[str]:
    """Загружает список прокси-серверов из файла или возвращает пустой список при отсутствии файла."""
    if file_proxy.exists():
        with open(file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        logger.info(f"Загружено {len(proxies)} прокси.")
        return proxies
    else:
        logger.warning("Файл с прокси не найден. Работаем без прокси.")
        return []  # Возвращаем пустой список, если файла нет

# Загрузка списка URL из CSV файла


def load_urls(file_path: Path) -> List[str]:
    """Загружает список URL из CSV файла."""
    df = pd.read_csv(file_path)
    if 'url' not in df.columns:
        raise ValueError("CSV файл должен содержать колонку 'url'.")
    return df['url'].tolist()


def parse_sitemap_index(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_links = [loc.text for loc in root.findall(
        "ns:sitemap/ns:loc", namespace)]
    return sitemap_links


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(10),
    retry=retry_if_exception_type(requests.RequestException),
)
def download_file(url: str, output_path: Path, proxies: List[str]) -> None:
    if proxies:
        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}
    else:
        proxies_dict = None  # Если прокси нет, делаем запрос без них

    try:
        response = requests.get(
            url,
            cookies=cookies,
            headers=headers,
            timeout=30,
            proxies=proxies_dict,
        )
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            logger.info(f"Скачали файл {url}")
        else:
            logger.error(f"Ошибка {response.status_code} при загрузке {url}")
    except requests.RequestException as e:
        if proxies_dict:
            logger.error(proxies_dict)
        logger.error(f"Ошибка при обработке запроса для URL {url}: {e}")
        raise


def write_csv(file_path, data):
    """Записывает данные в CSV файл с помощью pandas."""
    df = pd.DataFrame(data, columns=["url"])
    df.to_csv(file_path, index=False)
    logger.info(f"Записано {len(data)} ссылок в {file_path}")

# 3. Скачивание всех .xml.gz файлов в многопоточном режиме


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(5),
    retry=retry_if_exception_type(requests.RequestException),
)
# Скачивание всех .xml.gz файлов
def download_gz_files(links: List[str], output_dir: Path, proxies: Optional[List[str]], max_workers: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    def download_link(link: str) -> None:
        file_name = output_dir / Path(urlparse(link).path).name
        if not file_name.exists():  # Проверка на существование файла
            download_file(link, file_name, proxies)
        else:
            logger.info(f"Файл {file_name} уже существует, пропуск.")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(download_link, links)

# 4. Распаковка .xml.gz файлов


def extract_gz_files(input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for gz_file in input_dir.glob("*.gz"):
        output_file = output_dir / gz_file.stem  # Убираем ".gz"
        with gzip.open(gz_file, "rb") as f_in:
            with open(output_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)


def process_xml_files(input_dir: Path, output_csv: Path) -> None:
    input_dir = Path(input_dir)
    product_urls = set()  # Используем set для уникальных URL

    for xml_file in input_dir.glob("*.xml"):
        product_urls.update(parse_product_urls(xml_file)
                            )  # Добавляем уникальные URL

    # Преобразуем в список перед записью
    write_csv(output_csv, list(product_urls))


def parse_product_urls(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    product_urls = [loc.text for loc in root.findall(
        "ns:url/ns:loc", namespace)]
    return product_urls


def extract_and_save_specific_urls(input_csv: Path, output_csv: Path, substring: str) -> None:
    """
    Извлекает URL-адреса из input_csv, которые содержат заданную подстроку, и сохраняет их в output_csv.

    :param input_csv: Путь к исходному CSV файлу с URL-адресами.
    :param output_csv: Путь к новому CSV файлу для записи отфильтрованных URL-адресов.
    :param substring: Подстрока, которую должен содержать URL для отбора.
    """
    # Читаем исходный CSV файл
    df = pd.read_csv(input_csv)

    # Проверяем, что файл содержит колонку с URL, например, 'url'
    if 'url' not in df.columns:
        raise ValueError("CSV файл должен содержать колонку 'url'.")

    # Фильтруем URL-адреса, содержащие подстроку
    filtered_df = df[df['url'].str.contains(substring, na=False)]

    # Сохраняем отфильтрованные URL в новый CSV файл
    filtered_df.to_csv(output_csv, index=False)
    logger.info(f"Отфильтрованные URL сохранены в файл: {output_csv}")


# Разделение URL на группы для потоков
def split_urls_across_workers(urls: List[str], num_workers: int) -> List[List[str]]:
    """Разделяет список URL на группы для каждого потока."""
    chunk_size = len(urls) // num_workers
    return [urls[i * chunk_size: (i + 1) * chunk_size] for i in range(num_workers)]

# Сохранение HTML содержимого в файл


# Асинхронная функция для сохранения HTML содержимого в файл
async def save_html_file(html_content: str, output_dir: Path, url: str) -> None:
    """Асинхронно сохраняет HTML содержимое в файл, используя URL в качестве имени файла."""
    filename = output_dir / f"{urlparse(url).path.replace('/', '_')}.html"
    async with aiofiles.open(filename, "w", encoding="utf-8") as file:
        await file.write(html_content)
    logger.info(f"HTML файл сохранен: {filename}")

# Асинхронная функция для скачивания HTML с использованием прокси или без него


async def download_html(session: aiohttp.ClientSession, url: str, proxy: Optional[str] = None) -> Optional[str]:
    """Асинхронно скачивает HTML по заданному URL с использованием прокси или локально, если прокси отсутствуют."""
    try:
        async with session.get(url, proxy=proxy, timeout=30) as response:
            if response.status == 200:
                # Используем BeautifulSoup для проверки содержимого
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                h1_element = soup.find('h1')
                # Проверяем наличие <h1> с текстом "Шановний користувачу!"
                if h1_element and h1_element.text.strip() == "Шановний користувачу!":
                    logger.info(f"Пропуск сохранения для URL {
                                url}: обнаружен текст 'Шановний користувачу!'")
                    return None  # Пропускаем, если обнаружен данный текст
                return content
            else:
                logger.error(f"Ошибка {response.status} для URL {url}")
                return None
    except Exception as e:
        logger.error(f"Ошибка запроса для URL {url}: {e}")
        return None

# Асинхронная функция для пакетной загрузки HTML с очередью


async def async_download_html_with_proxies(urls: List[str], proxies: List[str], output_dir: Path, max_workers: int) -> None:
    queue = asyncio.Queue()
    for url in urls:
        await queue.put(url)  # Помещаем каждый URL в очередь

    async def worker() -> None:
        async with aiohttp.ClientSession() as session:
            while not queue.empty():
                # Извлекаем URL из очереди
                url = await queue.get()
                # Проверяем, существует ли файл для этого URL
                filename = output_dir / \
                    f"{urlparse(url).path.replace('/', '_')}.html"
                if filename.exists():
                    logger.info(
                        f"Файл {filename} уже существует, пропуск загрузки для URL {url}")
                    queue.task_done()  # Отмечаем задачу как выполненную, если файл уже существует
                    continue

                # Выбираем случайный прокси для каждого запроса
                proxy = random.choice(proxies) if proxies else None

                # Если файл не существует, загружаем HTML
                html_content = await download_html(session, url, proxy)
                if html_content:
                    await save_html_file(html_content, output_dir, url)
                queue.task_done()  # Сообщаем, что задача выполнена

    # Запускаем пул рабочих задач с учетом наличия прокси
    tasks = [worker() for _ in range(max_workers)]
    await asyncio.gather(*tasks)


def main():
    proxies = load_proxies()  # Загружаем прокси один раз в начале
    urls = load_urls(csv_all_edrs_products)
    max_workers = 50
    # substring = "https://clarity-project.info/edr/"  # Здесь задается фильтр
    # Шаг 1: Скачать основной файл sitemap-index.xml
    # download_file(SITEMAP_INDEX_URL, xml_sitemap, proxies)
    # logger.info("Скачали основной файл sitemap")

    # # Шаг 2: Парсинг и запись ссылок в CSV
    # sitemap_links = parse_sitemap_index(xml_sitemap)
    # write_csv(csv_url_site_maps, sitemap_links)
    # logger.info("Собрали ссылки для скачивания всех архивов gz")
    # # Шаг 3: Скачивание .xml.gz файлов
    # download_gz_files(sitemap_links, gz_directory, proxies, max_workers)
    # logger.info("Все архивы gz скачаны")
    # # Шаг 4: Распаковка .gz файлов
    # extract_gz_files(gz_directory, xml_directory)
    # logger.info("Все архивы gz распакованы")  # Исправлено

    # # Шаг 5: Парсинг URL продуктов из XML файлов
    # process_xml_files(xml_directory, csv_all_urls_products)
    # logger.info("Получили все ссылки на товары")
    # extract_and_save_specific_urls(
    #     csv_all_urls_products, csv_all_edrs_products, substring)
    # скачивание данных
    # Запуск асинхронной очереди
    asyncio.run(async_download_html_with_proxies(
        urls, proxies, html_files_directory, max_workers))
    logger.info("Загрузка завершена.")


if __name__ == "__main__":
    main()
