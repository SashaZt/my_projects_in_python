import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from config.logger import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = current_directory / "xml"
log_directory = current_directory / "log"
confi_directory = current_directory / "config"

data_directory.mkdir(parents=True, exist_ok=True)
confi_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"
urls_xml_file_path = data_directory / "urls_xml.csv"
urls_product_file_path = data_directory / "urls.csv"
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
URL_XML = config.get("url_xml")
COOKIES = config.get("cookies", {})
HEADERS = config.get("headers", {})
FILENAME_XML = urlparse(URL_XML).path.split("/")[-1]
XML_FILE_PATH = xml_directory / f"{FILENAME_XML}"


def download_with_curl(url, xml_file_path):
    """
    Скачивает файл по URL используя системную команду curl

    Returns:
        str or None: Путь к скачанному файлу или None в случае ошибки
    """
    try:

        # Создаем директорию, если она не существует

        logger.info(f"Начинаю скачивание файла с {url}")

        # Формируем команду curl
        command = [
            "curl",
            "-o",
            xml_file_path,  # Выходной файл
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
            logger.info(f"Файл успешно сохранен в: {xml_file_path}")
            return xml_file_path
        else:
            logger.error(f"Ошибка при скачивании файла: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return None


def download_all_xml():
    """
    Скачивает XML файл(ы) по указанному URL или списку URL.

    Args:
        urls (str или list): URL или список URL для скачивания XML файлов
        cookies (dict): Cookies для HTTP запроса
        headers (dict): Заголовки для HTTP запроса

    Returns:
        list или Path или None: Список путей к сохраненным файлам, путь к файлу или None в случае ошибки
    """
    # Чтение CSV-файла с URL
    urls_df = pd.read_csv(urls_xml_file_path, encoding="utf-8")
    urls = urls_df["url"].tolist()
    for url in urls:
        try:
            # Получаем имя файла из URL
            file_name = urlparse(url).path.split("/")[-1]
            xml_file_path = xml_directory / file_name
            logger.info(f"Скачиваем XML файл: {url}")

            download_with_curl(url, xml_file_path)
        except Exception as e:
            logger.error(f"Ошибка при обработке URL {url}: {e}")
            # Продолжаем со следующим URL


def parse_sitemap_urls():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    urls = []
    for xml_file in xml_directory.glob("jetsitemap-products-page-1*.xml"):
        try:
            # Парсим XML файл
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Ищем все элементы <url> в пространстве имён
            for url_elem in root.findall(
                ".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"
            ):
                loc = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if loc is not None:
                    urls.append(loc.text)

        except ET.ParseError as e:
            logger.error(f"Ошибка парсинга XML {xml_file}: {e}")
            return []
        except FileNotFoundError:
            logger.error(f"Файл {xml_file} не найден")
            return []

    logger.info(f"Найдено {len(urls)} URL-ов")

    # Сохранение в CSV
    if urls:  # Сохраняем только если есть URL
        url_data = pd.DataFrame(urls, columns=["url"])
        url_data.to_csv(urls_product_file_path, index=False)
        logger.info(f"URL сохранены в {urls_product_file_path}")


def parsin_xml(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        xml_content = file.read()

    # Парсим XML
    root = ET.fromstring(xml_content)

    # Находим все элементы <loc>
    product_sitemaps = []
    for sitemap in root.findall(
        ".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"
    ):
        loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        if loc is not None and "jetsitemap-products-page-" in loc.text:
            product_sitemaps.append(loc.text)
    url_data = pd.DataFrame(product_sitemaps, columns=["url"])
    url_data.to_csv(urls_xml_file_path, index=False)


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
    # download_xml(URL_XML, FILENAME_XML, COOKIES, HEADERS)
    # parsin_xml(XML_FILE_PATH)
    # download_all_xml()
    parse_sitemap_urls()

    # # Вывод итогов
    # logger.info("=== Итоги скачивания ===")
    # for url, file_path in results.items():
    #     status = "УСПЕШНО" if file_path else "ОШИБКА"
    # logger.info(f"{status}: {url}")
    # parse_si??temap_urls()
    # parsin_xml()
    # xml_temp()
