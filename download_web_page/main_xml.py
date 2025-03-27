import http.client
import os
import random
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pandas as pd
import requests
import wget
from loguru import logger

current_directory = Path.cwd()
xml_directory = current_directory / "xml"
log_directory = current_directory / "log"

log_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"

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


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def download_xml():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    response = requests.get(
        "https://xcore.com.ua/jetsitemap-products-page-4.xml",
        headers=headers,
        timeout=30,
    )
    save_path = "export_yandex_market.xml"
    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Файл успешно сохранен в: {save_path}")
    else:
        print(f"Ошибка при скачивании файла: {response.status_code}")


def parse_sitemap_urls():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    urls = []
    for xml_file in xml_directory.glob("*.xml"):
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

            # return urls

        except ET.ParseError as e:
            print(f"Ошибка парсинга XML: {e}")
            return []
        except FileNotFoundError:
            print(f"Файл {xml_file} не найден")
            return []
    logger.info(f"Найдено {len(urls)} URL-ов")


def parsin_xml():
    with open("sitemap_0.xml", "r", encoding="utf-8") as file:
        xml_content = file.read()

    root = ET.fromstring(xml_content)
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    urls = [
        url.text.strip()
        for url in root.findall(".//ns:loc", namespace)
        if not url.text.strip().startswith("https://bsspart.com/ru/")
    ]

    url_data = pd.DataFrame(urls, columns=["url"])
    url_data.to_csv("urls.csv", index=False)


def xml_temp():
    import xml.etree.ElementTree as ET

    import pandas as pd

    # Загрузка XML-файла
    xml_file = "index.xml"  # Укажите путь к вашему XML-файлу

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Найти секцию offers
    offers_section = root.find(".//offers")

    # Проверяем, что offers_section найден
    if offers_section is not None:
        # Извлекаем URL-адреса
        urls = [
            offer.find("url").text
            for offer in offers_section.findall("offer")
            if offer.find("url") is not None
        ]

        # Создаем DataFrame
        df = pd.DataFrame(urls, columns=["url"])

        # Сохраняем в CSV-файл
        csv_filename = "urls.csv"
        df.to_csv(csv_filename, index=False)

        print(f"Сохранено в {csv_filename}")
    else:
        print("Ошибка: Секция <offers> не найдена в XML.")


def httpx_client():
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    with httpx.Client() as client:
        response = client.get(
            "https://xcore.com.ua/jetsitemap-products-page-4.xml",
            headers=headers,
            timeout=30,
            follow_redirects=False,  # Отключаем редиректы
        )

        if response.status_code == 200:
            with open("export_yandex_market.xml", "wb") as file:
                file.write(response.content)
            print("Файл успешно сохранен")
        else:
            print(f"Ошибка при скачивании файла: {response.status_code}")


def download_with_wget_lib():
    """
    Скачивает файл по URL с помощью библиотеки wget

    Args:
        url (str): URL для скачивания файла
        download_dir (str): Директория для сохранения файла

    Returns:
        str or None: Путь к скачанному файлу или None в случае ошибки
    """
    try:
        url = "https://xcore.com.ua/jetsitemap-products-page-4.xml"
        # Создаем директорию, если она не существует
        os.makedirs(xml_directory, exist_ok=True)

        # Получаем имя файла из URL
        file_name = os.path.basename(urlparse(url).path)
        file_path = os.path.join(xml_directory, file_name)

        print(f"Начинаю скачивание файла с {url}")

        # Скачиваем файл
        downloaded_file = wget.download(url, out=file_path)
        print(f"\nФайл успешно сохранен в: {downloaded_file}")

        return downloaded_file
    except Exception as e:
        print(f"\nОшибка при скачивании файла: {e}")
        return None


def download_with_curl():
    """
    Скачивает файл по URL используя системную команду curl

    Returns:
        str or None: Путь к скачанному файлу или None в случае ошибки
    """
    try:

        # Создаем директорию, если она не существует

        # Получаем имя файла из URL
        file_name = os.path.basename(urlparse(url).path)
        file_path = os.path.join(xml_directory, file_name)

        print(f"Начинаю скачивание файла с {url}")

        # Формируем команду curl
        command = [
            "curl",
            "-o",
            file_path,  # Выходной файл
            "-L",  # Следовать редиректам
            "-A",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",  # User-Agent
            "--max-redirs",
            "10",  # Максимальное количество редиректов
            "--connect-timeout",
            "30",  # Тайм-аут соединения
            url,
        ]

        # Выполняем команду
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            print(f"Файл успешно сохранен в: {file_path}")
            return file_path
        else:
            print(f"Ошибка при скачивании файла: {result.stderr}")
            return None
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None


if __name__ == "__main__":
    # httpx_client()
    download_with_curl()
    # download_xml()
    # parse_sitemap_urls()
    # parsin_xml()
    # xml_temp()
