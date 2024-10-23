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

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_html():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    cookies = {
        "utag_main__ss": "0%3Bexp-session",
        "utag_main__pn": "2%3Bexp-session",
        "utag_main__se": "3%3Bexp-session",
        "utag_main__st": "1729593921919%3Bexp-session",
        "utag_main__prevCompletePageName": "005-idealista/portal > portal > viewAdDetail%3Bexp-1729595721922",
        "utag_main__prevLevel2": "005-idealista/portal%3Bexp-1729595721922",
        "__rtbh.uid": "%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22unknown%22%2C%22expiryDate%22%3A%222025-10-22T10%3A15%3A21.964Z%22%7D",
        "__rtbh.lid": "%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%225UwPp59AGnOAmGBz9OXT%22%2C%22expiryDate%22%3A%222025-10-22T10%3A15%3A21.964Z%22%7D",
        "cto_bundle": "BWMqL19oNDJ1NzhKJTJCS3hoN0s5NEpUTHFYd3J3V0JTS2JheGh2RmQ1bTJmckNvVmI4QXFJZiUyRmF0WHh6RTQwckNSaXBuZGdBalk2Sm8xV2FzVnluYjM5SSUyQmNacENzJTJCdXRWMFlrJTJCcnJkUmliWklLcHhKd0VxenZPcFBacyUyQjVjJTJGWENJeFpTbVJ2OTM3WkFoa0pLU014STljWDVwZTZNejJjdHAzZDN2Z3clMkYzWWs0cnk4JTNE",
        "datadome": "LImenFYjUTlzHiCc2qmBtzERceQovhpwadDXVmQKN6AMSQ~Y_1rzh5m5geDFn8M2oxrtOTcjCoyr~QGZiiUWUza8FdGKS0aTEFr4ap6l6DiaO9pOirRyHdQPBu~GuOqp",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    }
    url = "https://www.idealista.com/en/inmueble/106264161/"
    url_id = url.split("/")[-2]
    response = requests.get(
        url,
        cookies=cookies,
        headers=headers,
        proxies=proxies_dict,
    )

    # Проверка кода ответа
    if response.status_code == 200:
        all_data = parsing_html(response.text)
        # Сохранение HTML-страницы целиком
        with open("proba_0.html", "w", encoding="utf-8") as file:
            file.write(response.text)

        json_raw = get_phone(url_id, proxies_dict)
        if json_raw is not None:
            json_data = json_raw.json()
            number = json_data["phone1"]["number"]
            all_data["number"] = number

            logger.info(all_data)
    else:
        logger.error(response.status_code)


def get_phone(url_id, proxies_dict):
    cookies = {
        "datadome": "z6M7B7i1t4olYJ6jqgSvC0fp1_X7mVUggojZR_9RvvovTTmSJ0LTDsvqNyCnDnCaIC5Ty5tnvtL7MiZr3tMsIu7HU0dqEaVJbW9xsGsRMkPLjR1aAnjkWrVDkzXVeqiR",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru",
        "cache-control": "max-age=0",
        "dnt": "1",
        "priority": "u=0, i",
        "sec-ch-device-memory": "8",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-full-version-list": '"Google Chrome";v="129.0.6668.101", "Not=A?Brand";v="8.0.0.0", "Chromium";v="129.0.6668.101"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    }
    url = f"https://www.idealista.com/en/ajax/ads/{url_id}/contact-phones"
    response = requests.get(
        url,
        cookies=cookies,
        headers=headers,
        proxies=proxies_dict,
    )
    if response.status_code == 200:
        return response
    else:
        logger.error(response.status_code)
        return None


def parsing_html(content):

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


if __name__ == "__main__":
    get_html()
