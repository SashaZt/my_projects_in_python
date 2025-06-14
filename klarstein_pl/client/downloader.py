import re
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import pandas as pd
import requests
import urllib3
import asyncio
import aiohttp
import aiofiles
from aiohttp import ClientSession, ClientTimeout
import hashlib
import pandas as pd
from requests.exceptions import HTTPError
# from scrap import pars_htmls_multithreaded
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed,AsyncRetrying

from config import Config, logger, paths

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
config = Config.load()

MAX_WORKERS = int(config.client.max_workers)
URL_SITEMAP = config.client.url_sitemap
start_xml_path = paths.data / "sitemap.xml"
output_csv_file = paths.data / "output.csv"

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-user": "?1",
    "sec-gpc": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
}



def download_start_xml():
    """
    Скачиваем основной sitemap.xml
    """
    if not start_xml_path.exists():
        response = make_response(URL_SITEMAP)
        if response is not None:
            # Сохранение содержимого в файл
            with open(start_xml_path, "wb") as file:
                file.write(response.content)
        return response.content
    else:
        logger.info(f"Файл {start_xml_path} уже существует, пропускаем скачивание.")
        return start_xml_path.read_bytes()

def parse_start_xml():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>
    """
    download_start_xml()
    
    try:
        tree = ET.parse(start_xml_path)
        root = tree.getroot()

        matching_urls = []

        # Ищем все элементы, которые заканчиваются на 'url' (игнорируя namespace)
        for url_element in root.iter():
            if url_element.tag.endswith('url'):
                for child in url_element:
                    if child.tag.endswith('loc') and child.text:
                        if child.text.endswith(".html"):
                            matching_urls.append(child.text)
        
        save_all_urls(matching_urls)
        return matching_urls

    except FileNotFoundError:
        return []
    except ET.ParseError:
        return []

def save_all_urls(urls):
    """
    Сохраняет все найденные URL в CSV файл

    """

    logger.info(f"Найдено {len(urls)} URL-ов")
    url_data = pd.DataFrame(urls, columns=["url"])
    url_data.to_csv(output_csv_file, index=False)

@retry(
    stop=stop_after_attempt(10),
    wait=wait_fixed(10),
    retry=retry_if_exception_type(
        (HTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    ),
)
def make_response(url):
    proxies = {"https": config.client.proxy, "http": config.client.proxy}
    is_xml_file = url.lower().endswith(".xml")

    if is_xml_file:
        logger.debug("XML файл - запрос без прокси")
        proxies = None
    else:
        logger.debug("Обычный запрос - используем прокси")
        proxies = {"https": config.client.proxy, "http": config.client.proxy}

    response = requests.get(
        url, headers=headers, timeout=100, proxies=proxies, verify=False
    )
    if response.status_code == 200:
        return response
    else:
        logger.error(f"Ошибка при запросе по {url} Статус {response.status_code}")
        return None


def main_th():
    """
    Скачивание товаров
    """
    urls = []

    df = pd.read_csv(output_csv_file, encoding="utf-8")
    urls = df["url"].tolist()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for url in urls:
            file_name = f"{hashlib.md5(url.encode()).hexdigest()}"
            output_html_file = paths.html / f"{file_name}.html"
            if not output_html_file.exists():
                futures.append(executor.submit(get_html, url, output_html_file))
            else:
                print(f"Файл для {url} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            results.append(future.result())


def get_html(url, html_file):
    response = make_response(url)
    with open(html_file, "w", encoding="utf-8") as file:
        file.write(response.text)
    logger.info(html_file)

async def make_response_async(session, url, semaphore):
    """Асинхронный запрос с семафором для ограничения количества"""
    async with semaphore:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(2)
        ):
            with attempt:
                is_xml_file = url.lower().endswith(".xml")
                proxy = None if is_xml_file else config.client.proxy
                
                async with session.get(
                    url, 
                    headers=headers, 
                    timeout=ClientTimeout(total=100),
                    proxy=proxy,
                    ssl=False
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )

async def get_html_async(session, url, html_file, semaphore):
    """Асинхронное скачивание и сохранение HTML"""
    content = await make_response_async(session, url, semaphore)
    if content:
        async with aiofiles.open(html_file, 'w', encoding='utf-8') as file:
            await file.write(content)
        logger.info(f"Сохранен: {html_file}")
        return True
    return False

async def main_async():
    """Асинхронное скачивание товаров"""
    # Читаем URLs
    df = pd.read_csv(output_csv_file, encoding="utf-8")
    urls = df["url"].tolist()
    
    # Ограничиваем количество одновременных запросов
    MAX_CONCURRENT = 10  # Можете увеличить до 50-100
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    # Создаем сессию с переиспользованием соединений
    connector = aiohttp.TCPConnector(
        limit=100,  # Общий лимит соединений
        limit_per_host=20,  # Лимит на хост
        ttl_dns_cache=300,  # Кеш DNS
        use_dns_cache=True,
    )
    
    async with ClientSession(connector=connector) as session:
        tasks = []
        
        for url in urls:
            file_name = f"{hashlib.md5(url.encode()).hexdigest()}"
            output_html_file = paths.html / f"{file_name}.html"
            
            if not output_html_file.exists():
                task = get_html_async(session, url, output_html_file, semaphore)
                tasks.append(task)
            else:
                print(f"Файл для {url} уже существует, пропускаем.")
        
        # Выполняем все задачи
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Подсчитываем результаты
        successful = sum(1 for r in results if r is True)
        logger.info(f"Успешно скачано: {successful} из {len(tasks)}")
def run_async_download():
    asyncio.run(main_async())


if __name__ == "__main__":
    try:
        parse_start_xml()
        # main_th()
        # pars_htmls_multithreaded()

        # logger.info("✅ Все задачи завершены успешно!")
        # logger.info("❌ Остановите контейнер...")
        # time.sleep(600)
        # # Простая остановка контейнера
        # sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        sys.exit(1)
