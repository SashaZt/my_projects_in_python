import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from loguru import logger

current_directory = Path.cwd()
xml_directory = current_directory / "xml"
log_directory = current_directory / "log"
confi_directory = current_directory / "config"

confi_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"
config_file_path = confi_directory / "config.json"

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


def load_json_data(file_path):
    """Загрузка данных из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из {file_path}: {e}")
        return None


def save_json_data(data, file_path):
    """Сохранение данных в JSON файл"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {file_path}: {e}")
        return False


config = load_json_data(config_file_path)
URLS = config.get("competitor_www", [])
MY_URL = config.get("my_www")
HEADERS = config.get("headers", {})


def download_xml(url, headers, xml_dir=xml_directory):
    """
    Скачивает XML файл по указанному URL.

    Args:
        url (str): URL для скачивания XML файла
        headers (dict): Заголовки для HTTP запроса
        xml_dir (Path, optional): Директория для сохранения файлов. По умолчанию xml_directory.

    Returns:
        Path or None: Путь к сохраненному файлу или None в случае ошибки
    """
    try:
        # Извлечение имени файла из URL
        filename = urlparse(url).path.split("/")[-1]

        # Если имя файла пустое, используем домен
        if not filename:
            filename = urlparse(url).netloc.replace(".", "_")

        # Добавляем расширение .xml если его нет
        if not filename.endswith(".xml"):
            xml_file_path = xml_dir / f"{filename}.xml"
        else:
            xml_file_path = xml_dir / filename

        logger.info(f"Скачиваем XML файл: {url}")

        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

        # Проверка успешности запроса
        if response.status_code == 200:
            # Сохранение содержимого в файл
            with open(xml_file_path, "wb") as file:
                file.write(response.content)
            logger.info(f"Файл успешно сохранен в: {xml_file_path}")
            return xml_file_path
        else:
            logger.error(f"Ошибка при скачивании файла: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Исключение при скачивании файла {url}: {e}")
        return None


def download_all_xml_files(config_file_path):
    """
    Скачивает все XML файлы на основе конфигурации.

    Args:
        config_file_path (str): Путь к файлу конфигурации

    Returns:
        dict: Результаты скачивания {url: путь_к_файлу_или_None}
    """
    # Загрузка конфигурации

    results = {}

    # Скачивание файлов конкурентов
    for url in URLS:
        results[url] = download_xml(url, HEADERS)

    # Скачивание собственного файла
    if MY_URL:
        results[MY_URL] = download_xml(MY_URL, HEADERS)

    return results


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
    results = download_all_xml_files(config_file_path)

    # Вывод итогов
    logger.info("=== Итоги скачивания ===")
    for url, file_path in results.items():
        status = "УСПЕШНО" if file_path else "ОШИБКА"
        logger.info(f"{status}: {url}")
    # parse_si??temap_urls()
    # parsin_xml()
    # xml_temp()
