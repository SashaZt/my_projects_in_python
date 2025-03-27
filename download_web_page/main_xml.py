import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
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
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://jumper-cloud.fra1.digitaloceanspaces.com/34152937/export/yml/50/export_yandex_market.xml",
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


if __name__ == "__main__":
    download_xml()
    # parse_sitemap_urls()
    # parsin_xml()
    # xml_temp()
