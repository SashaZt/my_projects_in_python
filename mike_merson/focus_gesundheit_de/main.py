import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
from configuration.logger_setup import logger

# Базовый URL для запроса sitemap
BASE_URL = "https://www.focus-gesundheit.de/sitemap/sitemap.gesundheit.xml"

current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = current_directory / "xml"
html_directory = current_directory / "html"
# json_directory = current_directory / "json"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(exist_ok=True, parents=True)
# json_directory.mkdir(exist_ok=True, parents=True)
xml_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

start_sitemap = xml_directory / "sitemap.xml"
output_csv = data_directory / "output.csv"
all_url_sitemap = data_directory / "sitemap.csv"


def fetch_sitemap_links():
    """
    Загружает основной файл sitemap и извлекает ссылки на подкарты.
    """
    response = requests.get(BASE_URL, timeout=30)
    if response.status_code != 200:
        raise Exception(f"Ошибка при загрузке {BASE_URL}: {response.status_code}")

    # Парсим XML и извлекаем ссылки на подкарты
    root = ET.fromstring(response.content)
    namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_links = [elem.text for elem in root.findall(".//ns:loc", namespaces)]
    return [link for link in sitemap_links if "sitemap.gesundheit.entries" in link]


def download_and_parse_sitemaps(sitemap_links):
    """
    Скачивает файлы sitemap и извлекает ссылки, содержащие "/arzt".
    """
    arzt_links = []

    for link in sitemap_links:
        filename = xml_directory / Path(link).name
        response = requests.get(link, timeout=30)
        if response.status_code != 200:
            print(f"Ошибка загрузки {link}: {response.status_code}")
            continue

        # Сохраняем локально
        with open(filename, "wb") as file:
            file.write(response.content)
        print(f"Файл {filename} успешно загружен.")

        # Парсим XML для извлечения ссылок
        root = ET.fromstring(response.content)
        namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [elem.text for elem in root.findall(".//ns:loc", namespaces)]
        arzt_links.extend([url for url in urls if "/arzt" in url])

    return arzt_links


def save_to_csv(urls, output_file):
    """
    Сохраняет ссылки в CSV файл.
    """
    df = pd.DataFrame(urls, columns=["url"])
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"Результаты успешно сохранены в {output_file}")


def main():
    # Шаг 1: Получение ссылок на подкарты
    sitemap_links = fetch_sitemap_links()
    logger.info(f"Найдено {len(sitemap_links)} подкарт.")

    # Шаг 2: Скачивание файлов sitemap и извлечение ссылок
    arzt_links = download_and_parse_sitemaps(sitemap_links)
    logger.info(f"Найдено {len(arzt_links)} ссылок, содержащих '/arzt'.")

    # Шаг 3: Сохранение результатов в CSV файл
    save_to_csv(arzt_links, output_csv)


if __name__ == "__main__":
    main()
