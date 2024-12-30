import asyncio
import json
import os
import random
import re
import ssl
import xml.etree.ElementTree as ET
from base64 import b64decode
from pathlib import Path

import aiohttp
import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.poolmanager import PoolManager

current_directory = Path.cwd()

data_directory = current_directory / "data"
html_directory = current_directory / "html"

data_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)

output_csv_file = data_directory / "output.csv"


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_html_scraperapi():
    url = "https://www.idealista.com/en/inmueble/106264161/"
    apikey = "08ed3288dfca36359e9d28ddbe833829"
    url_id = url.split("/")[-2]

    payload = {"api_key": apikey, "url": url}
    response = requests.get("https://api.scraperapi.com", params=payload)
    # Проверка кода ответа
    if response.status_code == 200:
        all_data = parsing_html(response.text)
        # Сохранение HTML-страницы целиком
        with open("proba_0.html", "w", encoding="utf-8") as file:
            file.write(response.text)

        # json_raw = get_phone(url_id)
        # if json_raw is not None:
        #     json_data = json_raw.json()
        #     number = json_data["phone1"]["number"]
        #     all_data["number"] = number

        #     logger.info(all_data)
    else:
        logger.error(response.status_code)


def get_phone_scraperapi(url_id):
    apikey = "08ed3288dfca36359e9d28ddbe833829"

    url = f"https://www.idealista.com/en/ajax/ads/{url_id}/contact-phones"
    payload = {"api_key": apikey, "url": url}
    response = requests.get("https://api.scraperapi.com", params=payload)
    if response.status_code == 200:
        return response
    else:
        logger.error(response.status_code)
        return None


def get_html_zyte():
    url = "https://www.idealista.com/en/inmueble/106264161/"
    url_id = url.split("/")[-2]

    current_directory = Path.cwd()
    cert_file = current_directory / "zyte-ca.crt"
    response = requests.get(
        url,
        proxies={
            "http": "http://bfa6a820e75f4a97a39c74abfa6aeb3f:@api.zyte.com:8011/",
            "https": "http://bfa6a820e75f4a97a39c74abfa6aeb3f:@api.zyte.com:8011/",
        },
        verify=cert_file,
    )
    if response.status_code == 200:
        all_data = parsing_html(response.text)
        with open("proba_0.html", "w", encoding="utf-8") as file:
            file.write(response.text)
        # json_raw = get_phone_zyte(url_id)
        # if json_raw is not None:
        #     json_data = json_raw.json()
        #     number = json_data["phone1"]["number"]
        #     all_data["number"] = number

        logger.info(all_data)


def get_phone_zyte(url_id):

    url = f"https://www.idealista.com/en/ajax/ads/{url_id}/contact-phones"
    current_directory = Path.cwd()
    cert_file = current_directory / "zyte-ca.crt"
    response = requests.get(
        url,
        proxies={
            "http": "http://bfa6a820e75f4a97a39c74abfa6aeb3f:@api.zyte.com:8011/",
            "https": "http://bfa6a820e75f4a97a39c74abfa6aeb3f:@api.zyte.com:8011/",
        },
        verify=cert_file,
    )
    if response.status_code == 200:
        return response
    else:
        logger.error(response.status_code)
        return None


def parsing_html_req(content):

    soup = BeautifulSoup(content, "lxml")
    title = None
    location = None
    price = None
    description = None
    title_raw = soup.find("span", attrs={"class", "main-info__title-main"})
    if title_raw:
        title = title_raw.get_text(strip=True)
    location_raw = soup.find("span", attrs={"class", "main-info__title-minor"})
    if location_raw:
        location = location_raw.get_text(strip=True)
    price_raw = soup.find("span", attrs={"class", "h3-simulated txt-bold"})
    if price_raw:
        price = price_raw.get_text(strip=True)
    description_raw = soup.find(
        "div",
        attrs={
            "class",
            "adCommentsLanguage expandable is-expandable with-expander-button",
        },
    )
    if description_raw:
        description = description_raw.get_text(strip=True)
    list_items = soup.find_all("li", class_="header-map-list")

    values = [item.get_text(strip=True) for item in list_items]

    location = ", ".join(values)
    # Новый элемент - извлечение площади и количества комнат
    info_features = soup.find("div", class_="info-features").find_all("span")

    area = info_features[0].get_text(strip=True)
    number_of_rooms = info_features[1].get_text(strip=True).split()[0]

    all_data = {
        "title": title,
        "location": location,
        "price": price,
        "description": description,
        "location": location,
        "area": area,
        "number_of_rooms": number_of_rooms,
    }
    return all_data


def extract_photo(soup):
    all_data = []
    # Ищем теги <script> с данными
    script_tags = soup.find_all("script")

    for script in script_tags:
        if "fullScreenGalleryPics" in script.text:
            # Извлекаем содержимое с помощью регулярного выражения
            match = re.search(r"fullScreenGalleryPics\s*:\s*(\[[^\]]*\])", script.text)
            if match:
                gallery_data = match.group(1)
                # logger.info(f"Найденные данные match:\n{gallery_data}")
                try:
                    # Исправляем кавычки
                    gallery_data = gallery_data.replace("'", '"')

                    # Исправляем кавычки перед "https"
                    gallery_data = re.sub(r'""https://', r'"https://', gallery_data)

                    # Добавляем кавычки к ключам
                    gallery_data = re.sub(r"([{,])\s*(\w+):", r'\1 "\2":', gallery_data)

                    # Преобразуем в JSON
                    full_screen_gallery_pics = json.loads(gallery_data)
                    # logger.info(f"Данные из файла {html_file.name}:")

                    # Логируем ключевую информацию
                    for idx, pic in enumerate(full_screen_gallery_pics, start=1):
                        description = pic.get("hoverText", "Нет данных")
                        url = pic.get("imageDataService", "Нет данных")
                        dimensions = (
                            f"{pic.get('width', 'нет')}x{pic.get('height', 'нет')}"
                        )
                        tag = pic.get("tag", "Нет данных")
                        photos = {f"{description}_{idx}": url}
                        all_data.append(photos)
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Ошибка декодирования JSON в файле {html_file.name}: {e}"
                    )
                    logger.info(
                        f"Не удалось декодировать следующие данные:\n{gallery_data}"
                    )
    return all_data


# Функция для исправления формата JSON
def clean_and_fix_json(raw_text):
    # Заменяем одинарные кавычки на двойные
    raw_text = re.sub(r"'", r'"', raw_text)
    # Убираем лишние запятые перед закрывающими скобками
    raw_text = re.sub(r",\s*([\]}])", r"\1", raw_text)
    # Добавляем кавычки к ключам, если их нет
    raw_text = re.sub(r"(?<![\{\[,])\s*([a-zA-Z0-9_]+)\s*:\s*", r'"\1": ', raw_text)
    # Убираем лишние символы, если они есть в начале или конце
    raw_text = raw_text.strip()
    return raw_text


def parsing_html():
    output_file = Path("extracted_profile_data.json")
    extracted_data = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
        soup = BeautifulSoup(content, "lxml")
        title = None
        location = None
        price = None
        description = None
        area = None
        number_of_rooms = None
        imgs_title = None
        # Извлечение данных
        title = soup.find("span", class_="main-info__title-main")
        location = soup.find("span", class_="main-info__title-minor")
        price = soup.find("span", class_="info-data-price")
        description = soup.find(
            "div", class_="adCommentsLanguage expandable is-expandable"
        )

        title = title.get_text(strip=True) if title else None
        location = location.get_text(strip=True) if location else None
        price = price.get_text(strip=True) if price else None
        description = description.get_text(strip=True) if description else None

        list_items = soup.find_all("li", {"class": "header-map-list"})

        values = [item.get_text(strip=True) for item in list_items]

        location = ", ".join(values)

        # Извлечение характеристик (площадь, комнаты)
        area = None
        number_of_rooms = None
        info_features = soup.find("div", class_="info-features")
        if info_features:
            spans = info_features.find_all("span")
            if len(spans) >= 2:
                area = spans[0].get_text(strip=True)
                number_of_rooms = spans[1].get_text(strip=True).split()[0]

        imgs_title_raw = soup.find(
            "img", attrs={"class", "image-focus show image-focus show"}
        )
        if imgs_title_raw:
            imgs_title = imgs_title_raw.get("src")

        photos = extract_photo(soup)

        all_data = {
            "title": title,
            "imgs_title": imgs_title,
            "price": price,
            "description": description,
            "location": location,
            "area": area,
            "number_of_rooms": number_of_rooms,
            "photos": photos,
        }
        extracted_data.append(all_data)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # get_html_scraperapi()
    # get_html_zyte()
    parsing_html()
    # Загружаем файл
