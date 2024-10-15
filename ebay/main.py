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
html_page_directory = current_directory / "html_page"
html_product_directory = current_directory / "html_product"

data_directory.mkdir(parents=True, exist_ok=True)
html_page_directory.mkdir(parents=True, exist_ok=True)
html_product_directory.mkdir(parents=True, exist_ok=True)


output_csv_file = data_directory / "output.csv"
cookies = {
    "ak_bmsc": "C5461596E2A7551D119B11B9AC7B4A87~000000000000000000000000000000~YAAQXTYQYBs9gH+SAQAAxPTRihn+AWhsuWoyN3PCEJ+fTJzH0ZnsnOW9aAaAcJhh+dNSOA5b9vqesmudElEdoNe7JQS3USAIlHzsRC2IJWk94b0Bt46s+x0tC+g7T/poR9w2EESsABx19L08PmPOMcsmiCdb3+LZhDbBMxG2U+0lwoQDiWqoWzulDBjHY8nL8BCuYSNCFjjwf48QAv/IRLVTkyf6+eaOPzKv85nA0K0dKq0DVYJO0rptkbqPEncGlMlG28Q4D6Gen8YDK7rlR6N2KBPjZ9GBcRHbMAVQuWDO93Hg1YzT2VVnFpKNTmLoZxbjIcKlu88of3kJQusPXcEUHfiFCOX3A6PZYfMEHEQJ6XWib/GUOSH95Z7EhrEvfFFRHSm8ewc=",
    "__uzma": "a813fe6e-4491-4adc-8972-ae1f29622c57",
    "__uzmb": "1728905869",
    "__uzme": "4418",
    "__ssds": "2",
    "__ssuzjsr2": "a9be0cd8e",
    "__uzmaj2": "eca8cd22-91f6-4756-8945-30fc7a245ff1",
    "__uzmbj2": "1728907668",
    "__uzmlj2": "vehRS1XWx7PXFnOlzGCI5IIYSSnwKONU8KPr5HqVjRw=",
    "__uzmcj2": "397401627840",
    "__uzmdj2": "1728907742",
    "__uzmfj2": "7f600059d8118f-fb35-4b9a-b231-c5eec8132344172890766826474347-93cccfb72642079116",
    "__uzmc": "964824368662",
    "__uzmd": "1728907773",
    "__uzmf": "7f600059d8118f-fb35-4b9a-b231-c5eec813234417289058693161904250-82d27e64b8f6121743",
    "ds2": "",
    "dp1": "bpbf/%23e000e0000000000000000068ee3da7^bl/UA6acf7127^",
    "s": "CgAD4ACBnDlumOGFkMWYyYWQxOTIwYWE3Mjg4YzZkNzg2ZmZjZWU3OTYzYYV7",
    "bm_sv": "21120F2BFDB1FFC0111D0DA586896449~YAAQXTYQYJrdg3+SAQAAVKrvihlFIxBhhftqvbNXqeQIvVcIDc//7/BUH+91SIpDqBjv4H1IAFxzhaKuZd8FGSi+oYQGjelnJyc3Op30mrlgTMZCgQsxrR2nwcC+cnc4QW7pAVSiVCtegMzm3vyUGW3s8JIUmWFHBn3sOLARIi2CA0oslVG06GHZMjF/yIz/CIDX9/RNLnlBML+DAQYBfTpJpHiFSl6LPHTjJ9LJTPzmDdcHR89fYaAUpYf5Nk0=~1",
    "ebay": "%5Ejs%3D1%5Esbf%3D%23000200%5E",
    "nonsession": "BAQAAAZJU03gwAAaAADMABWjuPacxMDAwNQDKACBqz3EnOGFkMWYyYWQxOTIwYWE3Mjg4YzZkNzg2ZmZjZWU3OTYAywACZw0RLzU3wRAVOIbJdWDmdNsnQ3gKbiwS+a4*",
    "__deba": "RClCxlc-RAB_iiOQfM5Gy_nt8ZCdN4NU0i_9XqMIRiUeTMEOxatr74Hpx2Vek7S4XR8UW1J2_XMwSXzXGqPFGDSJTUEHeLCqHI7wQDliKL3OHHm_qoCVpJuFHpX8VWFKh28lda3_iYXrpK5b_jSZhA==",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-full-version": '"129.0.6668.90"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"15.0.0"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
}


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_page():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}
    for i in range(1, 49):
        params = {
            "_ipg": "72",
            "_pgn": i,
            "rt": "nc",
        }

        response = requests.get(
            "https://www.ebay.com/str/tema4x4",
            params=params,
            cookies=cookies,
            headers=headers,
            proxies=proxies_dict,
        )

        # Проверка кода ответа
        if response.status_code == 200:
            html_file_name = html_page_directory / f"proba_0{i}.html"
            # Сохранение HTML-страницы целиком
            with open(html_file_name, "w", encoding="utf-8") as file:
                file.write(response.text)
        logger.info(response.status_code)


# Получение индификатора товара, для получение всех ссылок на товары
def parsing_page():
    # Папка с HTML файлами
    # Множество для хранения уникальных itm_value
    unique_itm_values = set()

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_page_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            # Найти все <div> с классом 'str-quickview-button str-item-card__property-title'
            div_elements = soup.find_all(
                "div", class_="str-quickview-button str-item-card__property-title"
            )
            # Пройтись по каждому найденному элементу и извлечь itm из атрибута data-track
            for div in div_elements:
                data_track = div.get("data-track")
                if data_track:
                    # Преобразовать значение JSON обратно в словарь
                    data = json.loads(data_track.replace("&quot;", '"'))
                    itm_value = data.get("eventProperty", {}).get("itm")
                    if itm_value:
                        unique_itm_values.add(itm_value)

    # Создать список URL на основе уникальных itm_value
    urls = [f"https://www.ebay.com/itm/{itm_value}" for itm_value in unique_itm_values]

    # Создать DataFrame из списка URL
    df = pd.DataFrame(urls, columns=["url"])

    # Записать DataFrame в CSV файл
    df.to_csv(output_csv_file, index=False)


# Скачать все товары
def get_responses_html_product():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    # Загрузить список URL из CSV файла
    df = pd.read_csv(output_csv_file)

    # Пройтись по каждому URL и выполнить HTTP-запрос
    for url in df["url"]:
        try:
            response = requests.get(
                url, cookies=cookies, headers=headers, proxies=proxies_dict
            )
            if response.status_code == 200:
                id_product = url.split("/")[-1]
                html_file_name = html_product_directory / f"{id_product}.html"
                # Сохранение HTML-страницы целиком
                with open(html_file_name, "w", encoding="utf-8") as file:
                    file.write(response.text)
                logger.info(id_product)

                # Здесь можно добавить код для обработки ответа, если требуется
            else:
                print(
                    f"Ошибка при запросе {url}, код состояния: {response.status_code}"
                )
        except requests.RequestException as e:
            print(f"Ошибка при подключении к {url}: {e}")


def parsing_product():

    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    all_results = []
    # Список всех HTML файлов
    html_files = list(html_product_directory.glob("*.html"))
    total_urls = len(html_files)  # Общее количество файлов
    # Создаем прогресс-бар с использованием tqdm
    progress_bar = tqdm(
        total=total_urls,
        desc="Обработка файлов",
        bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
    )
    # Пройтись по каждому HTML файлу в папке
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files:
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
            # Создать объект BeautifulSoup
        file_name_without_extension = html_file.stem
        full_url = f"https://www.ebay.com/itm/{file_name_without_extension}"
        soup = BeautifulSoup(content, "lxml")

        title = None
        price_value = None
        available_count = None
        part_number = None
        iframe_text = None
        interchange_number = None
        oe_oem_part_number = None
        sold_count = None
        title_raw = soup.find(
            "span", attrs={"class": "ux-textspans ux-textspans--BOLD"}
        )
        if title_raw:
            title = title_raw.get_text(strip=True)
        # Найти div с классом 'x-bin-price__content'
        price_container = soup.find("div", attrs={"class": "x-bin-price__content"})

        # Найти span внутри price_container с классом 'ux-textspans' и извлечь текст
        if price_container:
            span = price_container.find("span", attrs={"class": "ux-textspans"})
            if span:
                price_text = span.get_text(strip=True)
                # Удалить все нечисловые символы и оставить только значение
                price_value = "".join(c for c in price_text if c.isdigit() or c == ".")

            # Найти div с классом 'x-quantity__availability' и id 'qtyAvailability'
        availability_container = soup.find(
            "div", attrs={"class": "x-quantity__availability", "id": "qtyAvailability"}
        )

        # Извлечь информацию из вложенных span элементов
        if availability_container:
            spans = availability_container.find_all(
                "span", attrs={"class": "ux-textspans ux-textspans--SECONDARY"}
            )

            for span in spans:
                span_text = span.get_text(strip=True)
                if "available" in span_text.lower():
                    available_count = "".join(c for c in span_text if c.isdigit())
                elif "sold" in span_text.lower():
                    sold_count = "".join(c for c in span_text if c.isdigit())
        # Найти элемент <dl> с data-testid 'ux-labels-values'
        # Найти все элементы <dl> с data-testid 'ux-labels-values'
        dl_containers = soup.find_all("dl", attrs={"data-testid": "ux-labels-values"})

        # Пройти по каждому <dl>, чтобы найти нужный <dt> и связанный с ним <dd>
        for dl in dl_containers:
            dt_label = dl.find("dt", class_="ux-labels-values__labels")
            if dt_label and "Manufacturer Part Number" in dt_label.get_text(strip=True):
                # Найти соответствующее значение в <dd>
                dd_value = dl.find("dd", class_="ux-labels-values__values")
                if dd_value:
                    part_number = dd_value.find("span", class_="ux-textspans").get_text(
                        strip=True
                    )
        # Найти элемент iframe и получить значение src
        iframe = soup.find("iframe", id="desc_ifr")
        if iframe:
            iframe_src = iframe.get("src")

            # Выполнить запрос к URL из src
            response = requests.get(
                iframe_src, cookies=cookies, headers=headers, proxies=proxies_dict
            )
            if response.status_code == 200:
                # Создать новый BeautifulSoup для содержимого iframe
                iframe_soup = BeautifulSoup(response.content, "html.parser")

                # Извлечь текст из содержимого
                iframe_text = iframe_soup.get_text(strip=True)
                # logger.info(iframe_text)
            else:
                logger.error(
                    f"Не удалось получить данные из iframe, код состояния: {response.status_code}"
                )
        # Найти все <dl> с data-testid 'ux-labels-values'
        dl_containers = soup.find_all("dl", attrs={"data-testid": "ux-labels-values"})

        # Пройтись по каждому найденному элементу <dl>
        for dl in dl_containers:
            # Найти метку <dt> и проверить текст на наличие нужных меток
            label_span = dl.find("dt", class_="ux-labels-values__labels").find(
                "span", class_="ux-textspans"
            )
            if label_span:
                label_text = label_span.get_text(strip=True)
                if label_text == "OE/OEM Part Number":
                    # Извлечь значение для OE/OEM Part Number
                    dd_value = dl.find("dd", class_="ux-labels-values__values")
                    if dd_value:
                        oe_oem_part_number = dd_value.find(
                            "span", class_="ux-textspans"
                        ).get_text(strip=True)
                        # print(f"OE/OEM Part Number: {oe_oem_part_number}")
                elif label_text == "Interchange Part Number":
                    # Извлечь значение для Interchange Part Number
                    dd_value = dl.find("dd", class_="ux-labels-values__values")
                    if dd_value:
                        interchange_number = dd_value.find(
                            "span", class_="ux-textspans"
                        ).get_text(strip=True)
                        # print(f"Interchange Part Number: {interchange_number}")
        all_data = {
            "title": title,
            "price": price_value,
            "available_count": available_count,
            "sold_count": sold_count,
            "part_number": part_number,
            "interchange_number": interchange_number,
            "oe_oem_part_number": oe_oem_part_number,
            "url": full_url,
            "description": iframe_text,
        }
        all_results.append(all_data)
        # Обновить прогресс-бар
        progress_bar.update(1)

    # Закрыть прогресс-бар после завершения работы
    progress_bar.close()

    # Создать DataFrame из данных
    df = pd.DataFrame(all_results)

    # Записать DataFrame в Excel файл
    df.to_excel("product_data.xlsx", index=False)
