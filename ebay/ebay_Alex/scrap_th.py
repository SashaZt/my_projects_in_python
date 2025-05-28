import concurrent.futures
import hashlib
import json
import queue
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from logger import logger
from requests.exceptions import HTTPError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

current_directory = Path.cwd()
data_directory = current_directory / "data"
config_directory = current_directory / "config"
data_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)

config_file = config_directory / "config.json"
cookies = {
    "__uzma": "48f63d0a-8f14-443b-8715-fcdba0ef603b",
    "__uzmb": "1728902698",
    "__uzme": "0335",
    "__uzmc": "256671941755",
    "__uzmd": "1742639115",
    "__uzmf": "7f600064f0eb3a-c548-42ca-b2b7-28f9559755a4172890269899113736416513-2a38b34a491a6dcd19",
    "AMP_MKTG_f93443b04c": "JTdCJTIycmVmZXJyZXIlMjIlM0ElMjJodHRwcyUzQSUyRiUyRnd3dy5nb29nbGUuY29tJTJGJTIyJTJDJTIycmVmZXJyaW5nX2RvbWFpbiUyMiUzQSUyMnd3dy5nb29nbGUuY29tJTIyJTdE",
    "AMP_f93443b04c": "JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjI1NWQ1NmQxMi1mOThiLTQ5MGEtYTUzMi00ZjEyZThiZTJkMGYlMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzQyNjM5MTE3MDMyJTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTc0MjYzOTExNzA1NCUyQyUyMmxhc3RFdmVudElkJTIyJTNBMiUyQyUyMnBhZ2VDb3VudGVyJTIyJTNBMSU3RA==",
    "dp1": "bbl/UA6ba0f710^",
    "nonsession": "BAQAAAZRXz2gmAAaAADMABWm/w5AyMTAwMADKACBroPcQOGFhMTk4MGYxOTIwYTZmMTZlM2QyZjUwZmZiNTE4YTYAywABZ96XGDbYNiX16bk46kVFvzpbH3uSlWh5Iw**",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "priority": "u=0, i",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-full-version": '"135.0.7049.115"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"19.0.0"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}

proxy_list = []


def load_proxies():
    """
    Загружает список прокси-серверов из config.json
    """
    global proxy_list
    try:
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)

                # Проверяем формат данных в config.json
                if "proxy_server" in config and isinstance(
                    config["proxy_server"], list
                ):
                    proxy_list = config["proxy_server"]
                    logger.info(
                        f"Загружено {len(proxy_list)} прокси-серверов из config.json"
                    )
                else:
                    logger.warning("В config.json отсутствует список прокси-серверов")
        else:
            logger.warning("Файл config.json не найден")
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации прокси: {str(e)}")


def get_random_proxy():
    """
    Возвращает случайный прокси из списка
    """
    if not proxy_list:
        return None

    proxy_url = random.choice(proxy_list)
    # Удаляем лишние пробелы в URL прокси (если они есть)
    proxy_url = proxy_url.strip()

    return {"http": proxy_url, "https": proxy_url}


# Декоратор для повторных попыток
# Декоратор для повторных попыток
@retry(
    stop=stop_after_attempt(10),  # Максимум 10 попыток
    wait=wait_fixed(10),  # Задержка 10 секунд между попытками
    retry=retry_if_exception_type(HTTPError),  # Повторять при HTTPError
)
def make_request(url, params=None):
    """
    Выполняет HTTP-запрос с автоматическими повторными попытками при ошибках.
    """
    # Получаем случайный прокси
    proxies = get_random_proxy()
    logger.info(proxies)
    response = requests.get(
        url,
        proxies=proxies,
        params=params,
        headers=headers,
        cookies=cookies,
        timeout=30,
    )
    response.raise_for_status()  # Вызывает HTTPError, если статус не 200

    return response.text


def get_breadcrumbList(soup):
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            # Получаем текст скрипта и проверяем его наличие
            script_text = script.string
            if not script_text or not script_text.strip():
                continue

            # Проверим, что это скрипт JSON-LD
            if "application/ld+json" not in script.get("type", ""):
                continue
            json_data = json.loads(script_text)
            # Проверяем, является ли это продуктом
            if isinstance(json_data, dict):
                # Проверяем тип - может быть строкой или списком типов
                product_type = json_data.get("@type")
                is_product = False

                if isinstance(product_type, str) and product_type == "BreadcrumbList":
                    is_product = True
                elif (
                    isinstance(product_type, list) and "BreadcrumbList" in product_type
                ):
                    is_product = True

                if is_product:
                    item_list = json_data.get("itemListElement", [])[-1]
                    name_category = item_list.get("name", "")
                    return name_category
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обработке скрипта: {str(e)}")


def get_url(soup):
    # 1. Извлекаем URL из <meta property="og:url">
    url_meta = soup.find("meta", {"property": "og:url"})
    url = url_meta.get("content", "") if url_meta else None
    return url


def get_price(soup):
    # 2. Извлекаем цену из <div class="x-price-primary">
    price_div = soup.find("div", {"class": "x-price-primary"})
    if price_div:
        price_text = price_div.find("span", {"class": "ux-textspans"}).get_text(
            strip=True
        )
        # Извлекаем числовое значение (например, "US $1,450.00" -> "1450.00")
        price = "".join(filter(lambda x: x.isdigit() or x == ".", price_text))
        return price
    else:
        return None


def get_title(soup):
    title_tag = soup.find("div", {"data-testid": "x-item-title"})
    if title_tag:
        title = title_tag.find("span").get_text(strip=True)
    else:
        title = None
    return title


def get_condition(soup):
    # 4. Извлекаем состояние товара
    condition_div = soup.find("div", {"class": "vim x-item-condition"})
    if condition_div:
        condition_text = condition_div.find(
            "span", {"data-testid": "ux-textual-display"}
        )
        condition = condition_text.get_text(strip=True) if condition_text else None
        return condition
    else:
        return None


def get_returns(soup):
    # 5. Извлекаем информацию о возврате
    returns_div = soup.find("div", {"data-testid": "x-returns-minview"})
    if not returns_div:
        # Если не нашли по data-testid, пробуем поискать по классу как запасной вариант
        returns_div = soup.find("div", {"class": "vim x-returns-minview"})

    if returns_div:
        # Ищем все элементы с текстом внутри блока возвратов
        returns_text = returns_div.find(
            "div", {"class": "ux-labels-values__values-content"}
        )
        if returns_text:
            # Собираем весь текст из дочерних элементов, соединяя пробелом
            # (вместо запятой, чтобы текст читался более естественно)
            returns_parts = []
            for child in returns_text.find_all(["span", "button"]):
                text = child.get_text(strip=True)
                if text:
                    returns_parts.append(text)

            # Соединяем все части текста
            returns = " ".join(returns_parts)
        else:
            returns = None
    else:
        returns = None

    return returns


def get_shipping(soup):
    # 6-7. Извлекаем информацию о доставке (Shipping и Delivery)
    shipping_container = soup.find("div", {"data-testid": "d-shipping-minview"})
    if not shipping_container:
        # Резервный поиск по классу
        shipping_container = soup.find("div", {"class": "vim d-shipping-minview"})

    if shipping_container:
        # Ищем Shipping внутри контейнера
        shipping_block = shipping_container.find(
            "div",
            {
                "data-testid": "ux-labels-values",
                "class": lambda c: c and "ux-labels-values--shipping" in c,
            },
        )
        if shipping_block:
            shipping_content = shipping_block.find(
                "div", {"class": "ux-labels-values__values-content"}
            )
            if shipping_content:
                # Обрабатываем первую строку с ценой и методом доставки
                first_line_parts = []
                for span in shipping_content.select(
                    "div:first-child > span.ux-textspans"
                ):
                    text = span.get_text(strip=True)
                    if text and not text.startswith("See details"):
                        first_line_parts.append(text)

                # Обрабатываем вторую строку с информацией о местоположении
                location_text = ""
                location_span = shipping_content.select_one(
                    "div:nth-child(2) > span.ux-textspans--SECONDARY"
                )
                if location_span:
                    location_text = location_span.get_text(strip=True)

                # Собираем всю информацию о доставке
                shipping_info = []
                if first_line_parts:
                    shipping_info.append(" ".join(first_line_parts))
                if location_text:
                    shipping_info.append(location_text)

                # Ищем информацию о комбинированной доставке
                combined_shipping = shipping_container.find(
                    "span",
                    string=lambda s: s and "Save on combined shipping" in s,
                )
                if combined_shipping:
                    shipping_info.append("Save on combined shipping")

                shipping = ", ".join(shipping_info)
            else:
                shipping = None
        else:
            shipping = None

        # Обработка информации о доставке (Delivery)
        delivery_block = shipping_container.find(
            "div", {"class": "ux-labels-values--deliverto"}
        )

        if delivery_block:
            delivery_content_div = delivery_block.find(
                "div", {"class": "ux-labels-values__values-content"}
            )
            if delivery_content_div:
                delivery_info = []

                # Первая строка - даты доставки
                first_div = delivery_content_div.find("div")

                if first_div:
                    delivery_text = ""

                    # Ищем основной текст и выделенные даты
                    main_spans = first_div.find_all(
                        "span", {"class": "ux-textspans"}, recursive=False
                    )

                    # Собираем текст и даты
                    for span in main_spans:
                        # Исключаем span-элементы, содержащие информационный всплывающий блок
                        if "ux-textspans__custom-view" not in span.get(
                            "class", []
                        ) and not span.has_attr("role"):
                            delivery_text += span.get_text(strip=True) + " "

                    if delivery_text.strip():
                        delivery_info.append(delivery_text.strip())

                # Вторая строка - примечание о сроках
                second_div = (
                    delivery_content_div.find_all("div")[1]
                    if len(delivery_content_div.find_all("div")) > 1
                    else None
                )
                if second_div:
                    notes = []
                    for span in second_div.find_all(
                        "span",
                        {"class": lambda c: c and "ux-textspans--SECONDARY" in c},
                    ):
                        notes.append(span.get_text(strip=True))

                    if notes:
                        delivery_info.append(" ".join(notes))

                # Третья строка - информация об отправке
                third_div = (
                    delivery_content_div.find_all("div")[2]
                    if len(delivery_content_div.find_all("div")) > 2
                    else None
                )
                if third_div:
                    shipping_info = []

                    # Собираем текст из всех span элементов
                    for span in third_div.find_all(
                        "span",
                        {"class": lambda c: c and "ux-textspans--SECONDARY" in c},
                    ):
                        shipping_info.append(span.get_text(strip=True))

                    # Собираем текст из всех ссылок
                    for link in third_div.find_all("a"):
                        span = link.find(
                            "span",
                            {"class": lambda c: c and "ux-textspans--SECONDARY" in c},
                        )
                        if span:
                            shipping_info.append(span.get_text(strip=True))

                    if shipping_info:
                        delivery_info.append(" ".join(shipping_info))

                # Собираем всю информацию в одну строку с разделителями
                delivery = ", ".join(delivery_info)
            else:
                delivery = None
        else:
            delivery = None
    else:
        shipping = None
        delivery = None

    return shipping, delivery


def get_specifications(soup):
    # 8. Извлекаем характеристики
    specifications = {}
    # spec_keys = set()

    # Метод 1: Извлечение из x-prp-product-details (первый формат)
    specs_div = soup.find("div", {"class": "x-prp-product-details"})

    if specs_div:
        spec_rows = specs_div.find_all("div", {"class": "x-prp-product-details_row"})
        for row in spec_rows:
            cols = row.find_all("div", {"class": "x-prp-product-details_col"})
            for col in cols:
                name = col.find("span", {"class": "x-prp-product-details_name"})
                value = col.find("span", {"class": "x-prp-product-details_value"})
                if name and value:
                    spec_name = name.get_text(strip=True)
                    spec_value = value.get_text(strip=True)
                    specifications[spec_name] = spec_value
                    # Добавляем ключ в множество всех ключей
                    # spec_keys.add(spec_name)

    # Метод 2: Извлечение из vim x-about-this-item (второй формат)
    if not specifications:
        about_item_div = soup.find("div", {"class": "vim x-about-this-item"})

        if about_item_div:
            spec_items = about_item_div.find_all("dl", {"class": "ux-labels-values"})

            for item in spec_items:
                # Находим название характеристики
                name_elem = item.find("dt", {"class": "ux-labels-values__labels"})
                if not name_elem:
                    continue

                spec_name = name_elem.get_text(strip=True)

                # Находим значение характеристики
                value_elem = item.find("dd", {"class": "ux-labels-values__values"})
                if not value_elem:
                    continue

                # Ищем первый div с текстом внутри значения
                value_content = value_elem.find(
                    "div", {"class": "ux-labels-values__values-content"}
                )
                if not value_content:
                    continue

                # Извлекаем только основной текст
                first_div = value_content.find("div")
                if not first_div:
                    continue

                # Обрабатываем обычный текст
                if first_div.find(
                    "span",
                    {"class": "ux-expandable-textual-display-block-inline"},
                ):
                    # Если есть кнопка Read more, получаем только первую часть текста
                    text_span = first_div.find("span", {"data-testid": "text"})
                    if text_span:
                        spec_value = text_span.get_text(strip=True)
                    else:
                        # Если нет span с data-testid="text", берем весь текст блока
                        spec_value = first_div.get_text(strip=True).split("Read more")[
                            0
                        ]
                else:
                    # Обычный текст, берем только текст из первого div
                    spec_value = first_div.get_text(strip=True)

                # Очищаем значение от служебных текстов
                if "Read more" in spec_value:
                    spec_value = spec_value.split("Read more")[0]
                if "Read Less" in spec_value:
                    spec_value = spec_value.split("Read Less")[0]

                # Удаляем возможные скрытые тексты
                spec_value = re.sub(r"opens in a new window or tab", "", spec_value)
                spec_value = re.sub(r"about the seller notes", "", spec_value)
                spec_value = re.sub(r"Read moreRead Less", "", spec_value)

                # Убираем лишние кавычки в начале и конце
                spec_value = spec_value.strip('"')

                # Сохраняем в словарь
                specifications[spec_name] = spec_value
                # Добавляем ключ в множество всех ключей
                # spec_keys.add(spec_name)
    return specifications


# def scrap_html():

#     # Список для хранения данных
#     data = []
#     # Множество для хранения всех уникальных ключей характеристик

    # files = list(html_directory.glob("*.html"))
#     # Проходим по всем HTML-файлам в папке
#     logger.info(f"Обработка {len(files)} HTML-файлов...")
#     count = 0
#     for html_file in files:
        # with html_file.open(encoding="utf-8") as file:
        #     content = file.read()

#             try:
#                 soup = BeautifulSoup(content, "lxml")

#                 # Инициализируем словарь для данных
#                 product_data = {"filename": html_file.name}
#                 breadcrumb = get_breadcrumbList(soup)
#                 product_data["category"] = breadcrumb

#                 product_url = get_url(soup)
#                 product_data["url"] = product_url


#                 product_price = get_price(soup)
#                 product_data["price"] = product_price
#                 product_title = get_title(soup)

#                 # 3. Извлекаем изображения (до 3) из <div class="ux-image-carousel-item image-treatment image">
#                 images = extract_image_urls(soup)
#                 product_data["image_1"] = images[0] if len(images) > 0 else ""
#                 product_data["image_2"] = images[1] if len(images) > 1 else ""
#                 product_data["image_3"] = images[2] if len(images) > 2 else ""

#                 product_condition = get_condition(soup)
#                 product_data["condition"] = product_condition

#                 product_returns = get_returns(soup)
#                 product_data["returns"] = product_returns
#                 shipping, delivery = get_shipping(soup)
#                 product_data["shipping"] = shipping
#                 product_data["delivery"] = delivery

#                 specifications, spec_keys = get_specifications(soup)
#                 product_data["specifications"] = json.dumps(specifications, ensure_ascii=False)


#                 # Добавляем характеристики как отдельные поля в product_data
#                 for key, value in specifications.items():
#                     product_data[key] = value
#                 count += 1
#                 print(f"Обработано {count} файлов", end="\r")
#                 # Добавляем данные в список
#                 data.append(product_data)

#             except Exception as e:
#                 logger.error(f"Ошибка при обработке {html_file.name}: {str(e)}")
#                 data.append(
#                     {
#                         "filename": html_file.name,
#                         "title": "",
#                         "url": "",
#                         "price": "",
#                         "image_1": "",
#                         "image_2": "",
#                         "image_3": "",
#                         "condition": "",
#                         "returns": "",
#                         "shipping": "",
#                         "delivery": "",
#                         "Condition": "",
#                         "Vehicle VIN": "",
#                         "Model": "",
#                         "Brand": "",
#                         "Manufacturer Part Number": "",
#                         "Codice ricambio originale OE/OEM": "",
#                         "Condition and Options": "",
#                         "Conditions & Options": "",
#                         "Conditions and Options": "",
#                         "Direct Replacement": "",
#                         "Herstellernummer": "",
#                         "Interchange 1": "",
#                         "Interchange 2": "",
#                         "Interchange 3": "",
#                         "Interchange Part Number": "",
#                         "Material": "",
#                         "Mounting Style": "",
#                         "Numer części OE/OEM": "",
#                         "O.E. Part Number": "",
#                         "OE/OEM Part Number": "",
#                         "OE/OEM Referenznummer(n)": "",
#                         "OEM NO.": "",
#                         "Original Part Number OE/OEM": "",
#                         "POP_MPN": "",
#                         "POP_Other Part Number": "",
#                         "Referenznummer(n) OE": "",
#                         "Referenznummer(n) OEM": "",
#                         "Vergleichsnummer": "",
#                     }
#                 )

#     # Создаем DataFrame с учетом всех возможных ключей характеристик
#     # Базовые колонки, которые есть у всех товаров
#     base_columns = [
#         "filename",
#         "title",
#         "category",
#         "url",
#         "price",
#         "image_1",
#         "image_2",
#         "image_3",
#         "condition",
#         "returns",
#         "shipping",
#         "delivery",
#         "Condition",
#         "Vehicle VIN",
#         "Model",
#         "Brand",
#         "Manufacturer Part Number",
#         "Codice ricambio originale OE/OEM",
#         "Condition and Options",
#         "Conditions & Options",
#         "Conditions and Options",
#         "Direct Replacement",
#         "Herstellernummer",
#         "Interchange 1",
#         "Interchange 2",
#         "Interchange 3",
#         "Interchange Part Number",
#         "Material",
#         "Mounting Style",
#         "Numer części OE/OEM",
#         "O.E. Part Number",
#         "OE/OEM Part Number",
#         "OE/OEM Referenznummer(n)",
#         "OEM NO.",
#         "Original Part Number OE/OEM",
#         "POP_MPN",
#         "POP_Other Part Number",
#         "Referenznummer(n) OE",
#         "Referenznummer(n) OEM",
#         "Vergleichsnummer",
#     ]
#     # del product_data["specifications"]
#     # Добавляем все уникальные ключи характеристик как отдельные колонки
#     all_columns = base_columns + sorted(spec_keys)

#     # Преобразуем данные в DataFrame, заполняя отсутствующие колонки пустыми строками
#     # и обрабатывая переносы строк
#     df_data = []
#     for item in data:
#         row = {}
#         for col in all_columns:
#             value = item.get(col, "")
#             # Заменяем переносы строк на пробелы или другой символ
#             if isinstance(value, str):
#                 value = value.replace("\n", " ").replace("\r", "")
#             row[col] = value
#         df_data.append(row)

#     df = pd.DataFrame(df_data, columns=all_columns)

#     # Используем quoting=csv.QUOTE_ALL, чтобы все поля были в кавычках
#     # и escapechar для экранирования специальных символов
#     import csv

#     df.to_csv(
#         "product_details.csv",
#         index=False,
#         encoding="utf-8",
#         sep=";",
#         quoting=csv.QUOTE_ALL,
#         escapechar="\\",
#         doublequote=True,
#         quotechar='"',
#     )

#     logger.info(
#         f"Обработано {len(data)} файлов, данные сохранены в product_details.csv"
#     )


# def scrap_html():
#     # Список для хранения данных
#     data = []

#     # Определяем нужные ключи
#     required_keys = [
#         "filename",
#         "title",
#         "category",
#         "url",
#         "product_id",
#         "price",
#         "url_image_1",
#         "url_image_2",
#         "url_image_3",
#         # "condition",
#         "returns",
#         "shipping",
#         "delivery",
#         "Condition",
#         "Vehicle VIN",
#         "Model",
#         "Model2",
#         "Brand",
#         "Manufacturer Part Number",
#         "Manufacturer Part Number2",
#         "Codice ricambio originale OE/OEM",
#         "Condition and Options",
#         "Conditions & Options",
#         "Conditions and Options",
#         "Direct Replacement",
#         "Herstellernummer",
#         "Interchange 1",
#         "Interchange 2",
#         "Interchange 3",
#         "Interchange Part Number",
#         "Material",
#         "Mounting Style",
#         "Numer części OE/OEM",
#         "O.E. Part Number",
#         "OE/OEM Part Number",
#         "OE/OEM Referenznummer(n)",
#         "OEM NO.",
#         "Original Part Number OE/OEM",
#         "POP_MPN",
#         "POP_Other Part Number",
#         "Referenznummer(n) OE",
#         "Referenznummer(n) OEM",
#         "Vergleichsnummer",
#     ]

#     files = list(html_directory.glob("*.html"))
#     logger.info(f"Обработка {len(files)} HTML-файлов...")
#     count = 0

#     for html_file in files[:1000]:
#         with html_file.open(encoding="utf-8") as file:
#             content = file.read()

#             try:
#                 soup = BeautifulSoup(content, "lxml")

#                 # Инициализируем словарь для данных
#                 product_data = {"filename": html_file.name}
#                 breadcrumb = get_breadcrumbList(soup)
#                 product_data["category"] = breadcrumb

#                 product_url = get_url(soup)
#                 product_data["url"] = product_url
#                 if product_url:
#                     match = re.search(r"itm/(\d+)", product_url)
#                     if match:
#                         item_id = match.group(1)
#                         product_data["product_id"] = item_id
#                     else:
#                         product_data["product_id"] = None
#                 product_price = get_price(soup)
#                 product_data["price"] = product_price

#                 product_title = get_title(soup)
#                 product_data["title"] = product_title

#                 # Извлекаем изображения
#                 images = extract_image_urls(soup)
#                 if not images:
#                     logger.warning(
#                         f"Изображения не найдены в {html_file.name}, пробуем старый метод"
#                     )
#                 product_data["url_image_1"] = images[0] if len(images) > 0 else ""
#                 product_data["url_image_2"] = images[1] if len(images) > 1 else ""
#                 product_data["url_image_3"] = images[2] if len(images) > 2 else ""

#                 # product_condition = get_condition(soup)
#                 # product_data["condition"] = product_condition

#                 product_returns = get_returns(soup)
#                 product_data["returns"] = product_returns

#                 shipping, delivery = get_shipping(soup)
#                 product_data["shipping"] = shipping
#                 product_data["delivery"] = delivery

#                 specifications = get_specifications(soup)
#                 # Обрабатываем Manufacturer Part Number и разделяем его если есть ~
#                 if "Manufacturer Part Number" in specifications:
#                     mpn_value = specifications["Manufacturer Part Number"]
#                     if isinstance(mpn_value, str) and "~" in mpn_value:
#                         # Разделяем по символу ~
#                         parts = mpn_value.split("~")
#                         if len(parts) >= 2:
#                             # Первая часть - Model2
#                             specifications["Model2"] = parts[0].strip()
#                             # Вторая часть - Manufacturer Part Number2
#                             specifications["Manufacturer Part Number2"] = parts[
#                                 1
#                             ].strip()
#                             # Оригинальное значение остается как есть
#                             # specifications["Manufacturer Part Number"] уже содержит полное значение

#                 # Добавляем характеристики как отдельные поля в product_data
#                 for key, value in specifications.items():
#                     product_data[key] = value

#                 # Обновляем список required_keys, добавляя новые ключи
#                 required_keys_updated = required_keys + [
#                     "Model2",
#                     "Manufacturer Part Number2",
#                 ]

#                 # Создаем финальный объект только с нужными ключами
#                 filtered_product = {}
#                 for key in required_keys_updated:
#                     value = product_data.get(key, "")
#                     # Очищаем значение от переносов строк
#                     if isinstance(value, str):
#                         value = value.replace("\n", " ").replace("\r", "")
#                     filtered_product[key] = value

#                 # # Добавляем характеристики как отдельные поля в product_data
#                 # for key, value in specifications.items():
#                 #     product_data[key] = value

#                 # # Создаем финальный объект только с нужными ключами
#                 # filtered_product = {}
#                 # for key in required_keys:
#                 #     value = product_data.get(key, "")
#                 #     # Очищаем значение от переносов строк
#                 #     if isinstance(value, str):
#                 #         value = value.replace("\n", " ").replace("\r", "")
#                 #     filtered_product[key] = value

#                 count += 1
#                 print(f"Обработано {count} файлов", end="\r")

#                 # Добавляем отфильтрованные данные в список
#                 data.append(filtered_product)

#             except Exception as e:
#                 logger.error(f"Ошибка при обработке {html_file.name}: {str(e)}")

#                 # Создаем объект с пустыми значениями при ошибке
#                 error_product = {}
#                 for key in required_keys:
#                     error_product[key] = ""
#                 error_product["filename"] = html_file.name

#                 data.append(error_product)

#     # logger.info(data)
#     # Сохраняем данные в JSON файл
#     with open("product_details.json", "w", encoding="utf-8") as json_file:
#         json.dump(data, json_file, ensure_ascii=False, indent=4)

#     logger.info(
#         f"Обработано {len(data)} файлов, данные сохранены в product_details.json"
#     )
#     # download_images_and_update_json(data)


def scrap_html():
    """Обертка для обратной совместимости"""
    return scrap_html_threaded(max_workers=10, max_files=1000)


def extract_image_urls(soup):
    """
    Извлекает до 3 URL изображений из HTML-страницы eBay товара.
    Сначала пробует извлечь из JSON-LD, потом использует старые методы.

    Args:
        soup: BeautifulSoup объект с HTML страницы

    Returns:
        list: Список URL изображений (до 3 шт.) в разрешении 960px
    """
    images = []
    seen_urls = set()  # Для отслеживания уникальных URL

    # Метод 1: Извлечение из JSON-LD (приоритетный метод)
    try:
        # Ищем script теги с type="application/ld+json"
        json_scripts = soup.find_all("script", {"type": "application/ld+json"})

        for script in json_scripts:
            if script.string:
                try:
                    json_data = json.loads(script.string)

                    # Вариант 1: JSON-LD это массив объектов
                    if isinstance(json_data, list):
                        for item in json_data:
                            if (
                                isinstance(item, dict)
                                and item.get("@type") == "Product"
                            ):
                                image_list = item.get("image", [])

                                for img_url in image_list[:3]:  # Берем первые 3
                                    if (
                                        img_url
                                        and img_url.strip()
                                        and img_url not in seen_urls
                                    ):
                                        # Конвертируем в 960px разрешение
                                        if "s-l" in img_url:
                                            img_url_960 = (
                                                img_url.replace(
                                                    "s-l1600.jpg", "s-l960.webp"
                                                )
                                                .replace("s-l1200.jpg", "s-l960.webp")
                                                .replace("s-l500.jpg", "s-l960.webp")
                                                .replace("s-l140.jpg", "s-l960.webp")
                                            )
                                            img_url = img_url_960

                                        seen_urls.add(img_url)
                                        images.append(img_url)

                                        if len(images) >= 3:
                                            break

                                # Если нашли изображения, выходим из цикла обработки объектов
                                if images:
                                    break

                    # Вариант 2: JSON-LD это объект
                    elif (
                        isinstance(json_data, dict)
                        and json_data.get("@type") == "Product"
                    ):
                        image_list = json_data.get("image", [])

                        for img_url in image_list[:3]:  # Берем первые 3
                            if img_url and img_url.strip() and img_url not in seen_urls:
                                # Конвертируем в 960px разрешение
                                if "s-l" in img_url:
                                    img_url_960 = (
                                        img_url.replace("s-l1600.jpg", "s-l960.webp")
                                        .replace("s-l1200.jpg", "s-l960.webp")
                                        .replace("s-l500.jpg", "s-l960.webp")
                                        .replace("s-l140.jpg", "s-l960.webp")
                                    )
                                    img_url = img_url_960

                                seen_urls.add(img_url)
                                images.append(img_url)

                                if len(images) >= 3:
                                    break

                    # Если нашли изображения в текущем скрипте, возвращаем их
                    if images:
                        return images[:3]

                except json.JSONDecodeError:
                    # Если JSON некорректный, продолжаем поиск
                    continue

    except Exception as e:
        # Если ошибка в JSON-LD методе, продолжаем со старыми методами
        pass


# Новая многопоточная функция парсинга одного файла
def parse_single_html_file(html_file_path, required_keys):
    """
    Парсит один HTML файл и возвращает данные товара

    Args:
        html_file_path: Path объект файла
        required_keys: список требуемых ключей

    Returns:
        dict: словарь с данными товара или None при ошибке
    """
    thread_id = threading.current_thread().ident

    try:
        with html_file_path.open(encoding="utf-8") as file:
            content = file.read()

        soup = BeautifulSoup(content, "lxml")

        # Инициализируем словарь для данных
        product_data = {"filename": html_file_path.name}

        # Парсим все данные (используем существующие функции)
        breadcrumb = get_breadcrumbList(soup)
        product_data["category"] = breadcrumb

        product_url = get_url(soup)
        product_data["url"] = product_url

        # Извлекаем product_id из URL
        if product_url:
            match = re.search(r"itm/(\d+)", product_url)
            if match:
                item_id = match.group(1)
                product_data["product_id"] = item_id
            else:
                product_data["product_id"] = None

        product_price = get_price(soup)
        product_data["price"] = product_price

        product_title = get_title(soup)
        product_data["title"] = product_title

        # Извлекаем изображения
        images = extract_image_urls(soup)
        product_data["url_image_1"] = images[0] if len(images) > 0 else ""
        product_data["url_image_2"] = images[1] if len(images) > 1 else ""
        product_data["url_image_3"] = images[2] if len(images) > 2 else ""

        product_returns = get_returns(soup)
        product_data["returns"] = product_returns

        shipping, delivery = get_shipping(soup)
        product_data["shipping"] = shipping
        product_data["delivery"] = delivery

        specifications = get_specifications(soup)

        # Обрабатываем Manufacturer Part Number и разделяем его если есть ~
        if "Manufacturer Part Number" in specifications:
            mpn_value = specifications["Manufacturer Part Number"]
            if isinstance(mpn_value, str) and "~" in mpn_value:
                parts = mpn_value.split("~")
                if len(parts) >= 2:
                    specifications["Model2"] = parts[0].strip()
                    specifications["Manufacturer Part Number2"] = parts[1].strip()

        # Добавляем характеристики как отдельные поля в product_data
        for key, value in specifications.items():
            product_data[key] = value

        # Создаем финальный объект только с нужными ключами
        filtered_product = {}
        for key in required_keys:
            value = product_data.get(key, "")
            # Очищаем значение от переносов строк
            if isinstance(value, str):
                value = value.replace("\n", " ").replace("\r", "")
            filtered_product[key] = value

        return {
            "success": True,
            "data": filtered_product,
            "filename": html_file_path.name,
        }

    except Exception as e:
        logger.error(
            f"Поток {thread_id}: Ошибка при обработке {html_file_path.name}: {str(e)}"
        )

        # Создаем объект с пустыми значениями при ошибке
        error_product = {}
        for key in required_keys:
            error_product[key] = ""
        error_product["filename"] = html_file_path.name

        return {
            "success": False,
            "data": error_product,
            "filename": html_file_path.name,
            "error": str(e),
        }


def scrap_html_threaded(max_workers=10, max_files=0):
    """
    Многопоточная функция парсинга HTML файлов

    Args:
        max_workers: количество потоков для парсинга
        max_files: максимальное количество файлов для обработки (0 = все файлы)
    """
    # Список для хранения данных
    data = []

    # Определяем нужные ключи
    required_keys = [
        "filename",
        "title",
        "category",
        "url",
        "product_id",
        "price",
        "url_image_1",
        "url_image_2",
        "url_image_3",
        "returns",
        "shipping",
        "delivery",
        "Condition",
        "Vehicle VIN",
        "Model",
        "Model2",
        "Brand",
        "Manufacturer Part Number",
        "Manufacturer Part Number2",
        "Codice ricambio originale OE/OEM",
        "Condition and Options",
        "Conditions & Options",
        "Conditions and Options",
        "Direct Replacement",
        "Herstellernummer",
        "Interchange 1",
        "Interchange 2",
        "Interchange 3",
        "Interchange Part Number",
        "Material",
        "Mounting Style",
        "Numer części OE/OEM",
        "O.E. Part Number",
        "OE/OEM Part Number",
        "OE/OEM Referenznummer(n)",
        "OEM NO.",
        "Original Part Number OE/OEM",
        "POP_MPN",
        "POP_Other Part Number",
        "Referenznummer(n) OE",
        "Referenznummer(n) OEM",
        "Vergleichsnummer",
    ]

    # Получаем список HTML файлов
    all_files = list(html_directory.glob("*.html"))

    # Если max_files = 0, обрабатываем все файлы
    if max_files == 0:
        files = all_files
        logger.info(
            f"Обработка ВСЕХ {len(files)} HTML-файлов в {max_workers} потоках..."
        )
    else:
        files = all_files[:max_files]
        logger.info(
            f"Обработка {len(files)} из {len(all_files)} HTML-файлов в {max_workers} потоках..."
        )

    success_count = 0
    error_count = 0

    # Многопоточная обработка
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Отправляем задачи на выполнение
        future_to_file = {
            executor.submit(parse_single_html_file, file_path, required_keys): file_path
            for file_path in files
        }

        # Обрабатываем результаты по мере выполнения
        for future in as_completed(future_to_file):
            result = future.result()

            if result["success"]:
                data.append(result["data"])
                success_count += 1
            else:
                data.append(result["data"])  # Добавляем даже с ошибками
                error_count += 1
                logger.warning(
                    f"Ошибка парсинга файла {result['filename']}: {result.get('error', 'Неизвестная ошибка')}"
                )

            # Показываем прогресс каждые 50 файлов
            total_processed = success_count + error_count
            if total_processed % 50 == 0:
                logger.info(
                    f"Обработано {total_processed}/{len(files)} файлов (успешно: {success_count}, ошибок: {error_count})"
                )

    # Финальная статистика
    logger.info(f"Парсинг завершен. Успешно: {success_count}, Ошибок: {error_count}")

    # Сохраняем данные в JSON файл
    with open("product_details.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

    logger.info(
        f"Обработано {len(data)} файлов, данные сохранены в product_details.json"
    )

    return data


if __name__ == "__main__":
    # scrap_html()
    scrap_html_threaded(max_workers=40, max_files=0)
