import requests
import json
import aiohttp
import asyncio
import re
import requests
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from configuration.logger_setup import logger
import random
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import xml.etree.ElementTree as ET
import os
from tqdm import tqdm
from base64 import b64decode


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


def parsing_html():
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
        title_raw = soup.find("span", attrs={"class", "main-info__title-main"})
        if title_raw:
            title = title_raw.get_text(strip=True)
        location_raw = soup.find("span", attrs={"class", "main-info__title-minor"})
        if location_raw:
            location = location_raw.get_text(strip=True)
        price_raw = soup.find("span", attrs={"class", "info-data-price"})
        if price_raw:
            price = price_raw.get_text(strip=True)

        description_raw = soup.find(
            "div",
            attrs={
                "class",
                "adCommentsLanguage expandable is-expandable",
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

        imgs_raw = soup.find("div", attrs={"class", "images-slider large"})
        # if imgs_raw:

        all_data = {
            "title": title,
            "location": location,
            "price": price,
            "description": description,
            "location": location,
            "area": area,
            "number_of_rooms": number_of_rooms,
        }
        logger.info(imgs_raw)


if __name__ == "__main__":
    # get_html_scraperapi()
    # get_html_zyte()
    parsing_html()
