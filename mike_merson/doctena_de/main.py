import ast
import asyncio
import json
import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import demjson3
import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from dotenv import load_dotenv

env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
api_key = os.getenv("API_KEY")
# Настройте максимальное количество попыток, если требуется
MAX_RETRIES = 30
RETRY_DELAY = 30  # Задержка между попытками в секундах

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = current_directory / "xml"
html_directory = current_directory / "html"
json_directory = current_directory / "json"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(exist_ok=True, parents=True)
json_directory.mkdir(exist_ok=True, parents=True)
xml_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

start_sitemap = xml_directory / "sitemap.xml"
all_urls_page = data_directory / "all_urls.csv"
all_url_sitemap = data_directory / "sitemap.csv"


def read_csv(file):
    # Читаем файл start_sitemap.csv и возвращаем список URL
    df = pd.read_csv(file)
    return df["url"].tolist()


def extract_urls_from_xml_files():

    # Создаем пустое множество для уникальных URL
    unique_urls = set()

    # Проходим по всем XML файлам в указанной директории
    for xml_file in Path(xml_directory).glob("*.xml"):
        with xml_file.open(encoding="utf-8") as file:
            content = file.read()
            # Парсим XML содержимое
            root = ET.fromstring(content)
            namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            urls = [elem.text.strip() for elem in root.findall(".//ns:loc", namespaces)]
            unique_urls.update(urls)

    # Записываем уникальные URL в all_urls.csv
    df = pd.DataFrame({"url": list(unique_urls)})
    df.to_csv(all_urls_page, index=False)


if __name__ == "__main__":
    extract_urls_from_xml_files()
