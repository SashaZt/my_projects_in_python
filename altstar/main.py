import csv
import json
import random
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)


def get_html():
    cookies = {
        "PHPSESSID": "4u34v9cjpr22r449jev8j5ho40",
        "PHPSESSID": "4u34v9cjpr22r449jev8j5ho40",
        "PHPSESSID": "4u34v9cjpr22r449jev8j5ho40",
        "language": "uk-ua",
        "currency": "UAH",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://altstar.ua/vtyaguyuche-rele-startera",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://altstar.ua/zm599/zm", cookies=cookies, headers=headers, timeout=30
    )
    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open(output_html_file, "w", encoding="utf-8") as file:
            file.write(response.text)
        logger.info(f"Successfully saved {output_html_file}")
    else:
        logger.error(f"Failed to get HTML. Status code: {response.status_code}")


def scrap_html():
    with open("freepik.html", "r", encoding="utf-8") as file:
        content = file.read()
    soup = BeautifulSoup(content, "lxml")
    # Находим все элементы <figure> с классом "$relative"
    figures = soup.find_all("figure", class_="$relative")

    # Список для хранения результатов
    results = []

    # Проходим по всем найденным <figure>
    for figure in figures:
        # Ищем <img> внутри каждого <figure>
        img = figure.find("img")
        if img:
            # Извлекаем атрибуты alt и src
            alt_text = img.get("alt", "")  # Если alt отсутствует, вернем пустую строку
            src_url = img.get("src", "")  # Если src отсутствует, вернем пустую строку
            results.append({"alt": alt_text, "src": src_url})

    # Выводим результаты
    for result in results:
        print(f"Alt: {result['alt']}")
        print(f"Src: {result['src']}")
        print("---")

    # Если нужно сохранить в список словарей или файл, вот пример:
    import json

    with open("image_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # scrap_html()
    # main_realoem()
    # get_htmls()
    get_html()
