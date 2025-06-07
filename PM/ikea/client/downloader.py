import re
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
import urllib3
from requests.exceptions import HTTPError
from scrap import pars_htmls_multithreaded
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from config import Config, logger, paths

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
config = Config.load()

MAX_WORKERS = int(config.client.max_workers)

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


@retry(
    stop=stop_after_attempt(10),
    wait=wait_fixed(10),
    retry=retry_if_exception_type(
        (HTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    ),
)
def make_response(url):
    proxies = {"https": config.client.proxy, "http": config.client.proxy}
    # Проверяем заканчивается ли URL на .xml
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


def download_start_xml():
    """
    Скачиваем основной sitemap.xml
    """
    url = "https://www.ikea.com/sitemaps/sitemap.xml"
    if not start_xml_path.exists():
        response = make_response(url)
        if response is not None:
            # Сохранение содержимого в файл
            with open(start_xml_path, "wb") as file:
                file.write(response.content)


def parse_start_xml():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    download_start_xml()
    target = "https://www.ikea.com/sitemaps/prod-pl-PL_"
    try:
        # Парсим XML файл
        tree = ET.parse(start_xml_path)
        root = tree.getroot()

        # Определяем пространство имен (namespace), если оно есть
        namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Ищем все теги <url> и извлекаем <loc>
        matching_urls = [
            url.text
            for url in root.findall(".//sitemap:loc", namespace)
            if url.text and target in url.text
        ]
        return matching_urls

    except FileNotFoundError:
        return []


def download_all_xml():
    """
    Скачиваем
    """
    urls = parse_start_xml()
    for url in urls:

        file_name = Path(urlparse(url).path).name
        file_path = paths.data / file_name
        if not file_path.exists():
            response = make_response(url)
            if response is not None:
                with open(file_path, "wb") as file:
                    file.write(response.content)
                logger.info(file_path)

    parse_all_sitemap_urls()


def parse_all_sitemap_urls():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    urls = []
    for xml_file in paths.data.glob("prod*.xml"):
        try:
            # Парсим XML файл
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Определяем пространство имен (namespace), если оно есть
            namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Ищем все теги <url> и извлекаем <loc>
            for url in root.findall(".//sitemap:url", namespace):
                loc = url.find("sitemap:loc", namespace)

                if loc is not None and loc.text:
                    urls.append(loc.text)

        except ET.ParseError as e:
            logger.error(f"Ошибка парсинга XML: {e}")
            return []
        except FileNotFoundError:
            logger.error(f"Файл {xml_file} не найден")
            return []
    logger.info(f"Найдено {len(urls)} URL-ов")
    url_data = pd.DataFrame(urls, columns=["url"])
    url_data.to_csv(output_csv_file, index=False)


def format_product_code(url):
    # Извлекаем цифры из конца URL с помощью регулярного выражения
    match = re.search(r"(\d+)$", url.rstrip("/"))
    if match:
        code = match.group(1)
        # Форматируем код: первые 3 цифры, затем 3 цифры, затем 2 цифры
        if len(code) == 8:
            return f"{code[:3]}.{code[3:6]}.{code[6:]}"
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
        for url in urls[:41]:
            file_name = format_product_code(url)
            output_html_file = paths.html / f"{file_name}.html"
            if not output_html_file.exists():
                futures.append(executor.submit(get_html, url, output_html_file))
            else:
                print(f"Файл для {url} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            # Здесь вы можете обрабатывать результаты по мере их завершения
            results.append(future.result())


def get_html(url, html_file):
    response = make_response(url)
    with open(html_file, "w", encoding="utf-8") as file:
        file.write(response.text)
    logger.info(html_file)


if __name__ == "__main__":
    try:
        download_all_xml()
        main_th()
        pars_htmls_multithreaded()

        logger.info("✅ Все задачи завершены успешно!")
        logger.info("❌ Остановите контейнер...")
        time.sleep(600)
        # Простая остановка контейнера
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        sys.exit(1)
