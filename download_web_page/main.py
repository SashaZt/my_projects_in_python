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

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "1000 ip.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_html():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    cookies = {
        "G_ENABLED_IDPS": "google",
        "PHPSESSID": "ghjh4kef1sircto610lnisq8a5",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 'Cookie': 'G_ENABLED_IDPS=google; PHPSESSID=ghjh4kef1sircto610lnisq8a5',
        "DNT": "1",
        "Pragma": "no-cache",
        "Referer": "https://www.ua-region.com.ua/comments/01353858",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    response = requests.get(
        "https://www.ua-region.com.ua/01353858", cookies=cookies, headers=headers
    )

    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("proba.html", "w", encoding="utf-8") as file:
            file.write(response.text)
    print(response.status_code)


def get_json():

    response = requests.post(
        "https://prom.ua/graphql", cookies=cookies, headers=headers, json=json_data
    )

    # Проверка кода ответа
    if response.status_code == 200:
        json_data = response.json()
        # filename = os.path.join(json_path, f"0.json")
        with open("proba.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    else:
        print(response.status_code)


def download_xml():
    save_path = "sitemap.products.xml"
    url = "https://www.ua-region.com.ua/sitemap.xml"
    cookies = {
        "G_ENABLED_IDPS": "google",
        "PHPSESSID": "d7tptvp0pdt9s2n4eo585c7tp1",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 'Cookie': 'G_ENABLED_IDPS=google; PHPSESSID=d7tptvp0pdt9s2n4eo585c7tp1',
        "DNT": "1",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    # Отправка GET-запроса на указанный URL
    response = requests.get(url, cookies=cookies, headers=headers)

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Файл успешно сохранен в: {save_path}")
    else:
        print(f"Ошибка при скачивании файла: {response.status_code}")


# Функция для очистки данных
def clean_text(text):
    # Убираем лишние пробелы и символы \xa0
    cleaned_text = text.replace("\xa0", " ").strip()
    # Убираем заголовки, если они присутствуют
    cleaned_text = re.sub(
        r"^(Код ЄДРПОУ|Дата реєстрації|Дата оновлення)", "", cleaned_text
    )
    return cleaned_text.strip()


def parsing():
    with open("proba.html", encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")

    # Список для хранения всех единиц данных
    all_results = []

    # Безопасное извлечение заголовка страницы
    page_title_raw = soup.select_one("#main > div:nth-child(1) > div > h1")
    page_title = page_title_raw.get_text(strip=True) if page_title_raw else None

    # Безопасное извлечение юридического адреса
    legal_address_raw = soup.select_one(
        "#main > div.cart-company-full.container.pb-5 > div.row.flex-row-reverse > div.col-xl-9 > div.px-3.pb-3.px-md-4.pb-md-4.info_block.rounded.border.mt-3 > div.row > div.col-md-8 > div > div:nth-child(2) > div"
    )
    legal_address = (
        legal_address_raw.get_text(strip=True) if legal_address_raw else None
    )

    # Безопасное извлечение номера телефона компании
    phone_company_raw = soup.select_one(
        "#main > div.cart-company-full.container.pb-5 > div.row.flex-row-reverse > div.col-xl-9 > div.px-3.pb-3.px-md-4.pb-md-4.info_block.rounded.border.mt-3 > div.row > div.col-md-8 > div > div:nth-child(3) > div"
    )
    phone_company = (
        phone_company_raw.get_text(strip=True) if phone_company_raw else None
    )

    # Безопасное извлечение кода ЕДРПОУ
    cod_edrpo_raw = soup.select_one(
        "#main > div.cart-company-full.container.pb-5 > div.row.flex-row-reverse > div.col-xl-9 > div.px-3.pb-3.px-md-4.pb-md-4.info_block.rounded.border.mt-3 > div.row > div.col-md-4.mt-4.company-sidebar-info > div.company-sidebar.border.rounded.p-3.p-md-4.mb-3 > div:nth-child(2)"
    )
    cod_edrpo = cod_edrpo_raw.get_text(strip=True) if cod_edrpo_raw else None

    # Безопасное извлечение даты регистрации
    date_of_registration_raw = soup.select_one(
        "#main > div.cart-company-full.container.pb-5 > div.row.flex-row-reverse > div.col-xl-9 > div.px-3.pb-3.px-md-4.pb-md-4.info_block.rounded.border.mt-3 > div.row > div.col-md-4.mt-4.company-sidebar-info > div.company-sidebar.border.rounded.p-3.p-md-4.mb-3 > div:nth-child(3)"
    )
    date_of_registration = (
        date_of_registration_raw.get_text(strip=True)
        if date_of_registration_raw
        else None
    )

    # Безопасное извлечение даты обновления
    update_date_raw = soup.select_one(
        "#main > div.cart-company-full.container.pb-5 > div.row.flex-row-reverse > div.col-xl-9 > div.px-3.pb-3.px-md-4.pb-md-4.info_block.rounded.border.mt-3 > div.row > div.col-md-4.mt-4.company-sidebar-info > div.company-sidebar.border.rounded.p-3.p-md-4.mb-3 > div:nth-child(4)"
    )
    update_date = update_date_raw.get_text(strip=True) if update_date_raw else None
    # Словарь для текущей единицы данных
    # Находим все элементы <a> с атрибутом href, содержащим '/kved/'
    kved_elements = soup.select('a[href^="/kved/"]')

    # Извлекаем коды КВЕД и записываем их в список
    kved_list = [element["href"].split("/kved/")[1] for element in kved_elements]

    # Объединяем все коды в одну строку, разделенную запятыми
    kved_string = ",".join(kved_list)

    results = {
        "page_title": page_title,
        "legal_address": legal_address,
        "phone_company": phone_company,
        "cod_edrpo": cod_edrpo,
        "date_of_registration": date_of_registration,
        "update_date": update_date,
        "kved": kved_string,
    }
    cleaned_data = {key: clean_text(value) for key, value in results.items()}
    all_results.append(cleaned_data)
    logger.info(all_results)

    # # Ищем количество работников
    # number_of_employees = None
    # employee_label = soup.find("td", string="Кількість працівників")
    # if employee_label:
    #     number_of_employees = employee_label.find_next_sibling("td").string.strip()

    # # Ищем КАТОТТГ
    # katottg = None
    # katottg_label = soup.find("td", string="КАТОТТГ")
    # if katottg_label:
    #     katottg = katottg_label.find_next_sibling("td").string.strip()

    # # Словарь для текущей единицы данных
    # results = {
    #     "page_title": page_title,
    #     "number_of_employees": number_of_employees,
    #     "katottg": katottg,
    # }

    # # Добавляем словарь в список all_results
    # all_results.append(results)

    # # Выводим список словарей
    # print(nobr_start, nobr_end)

    # # Пример записи в Excel через pandas
    # df = pd.DataFrame(all_results)
    # df.to_excel("financial_data.xlsx", index=False, engine="openpyxl")

    # Выводим результат
    # page_title_h3 = soup.select_one(
    #     "#ProductInfo-template--19203350364488__main > div.product__subtitle > h3"
    # ).text
    # # description = soup.select_one(
    # #     "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(3) > div > div > div > div > div:nth-child(1) > div"
    # # ).text.replace("Description", "")
    # price = soup.select_one(
    #     "#price-template--19203350364488__main > div > div > div.price__regular > span.price-item.price-item--regular"
    # ).text.strip()
    # all_product_info = soup.select_one("#ProductAccordion-product_information > ul")
    # info_01 = all_product_info.select_one("li:nth-child(1)").text.strip()
    # # Второй элемент — Dimensions
    # info_02 = all_product_info.find(
    #     "li", string=lambda text: "Dimensions" in text
    # ).text.strip()

    # # Третий элемент — Weight
    # info_03 = all_product_info.find(
    #     "li", string=lambda text: "Weight" in text
    # ).text.strip()

    # # Четвертый элемент — Handcrafted
    # info_04 = all_product_info.find(
    #     "li", string=lambda text: "Handcrafted" in text
    # ).text.strip()
    # fotos = soup.find_all(
    #     "div", attrs=("class", "product__media media media--transparent")
    # )
    # for foto in fotos:
    #     img_tag = foto.find("img")
    #     if img_tag:
    #         src = img_tag.get("src")
    #         # Обрезаем строку по символу '?'
    #         clean_src = src.split("?")[0]
    #         clean_src = f"https:{clean_src}"
    #         logger.info(clean_src)

    # sku_item_n = soup.select_one(
    #     "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(2) > div"
    # ).text.replace("Item No.", "")
    # upc = soup.select_one(
    #     "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(4) > div > span:nth-child(2)"
    # ).text
    # brand = soup.select_one(
    #     "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(3) > div > span:nth-child(2)"
    # ).text


def parsing_xml():
    # Путь к файлу XML
    save_path = "sitemap.products.xml"

    # Открываем и парсим XML-файл
    tree = ET.parse(save_path)
    root = tree.getroot()

    # Определение пространства имен
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Извлечение всех тегов <loc>
    locations = root.findall(".//ns:loc", namespace)

    # Регулярное выражение для поиска нужных URL
    pattern = r"https://www\.ua-region\.com\.ua/sitemap/sitemap_\d+\.xml"

    # Генератор списков для получения всех URL, соответствующих регулярному выражению
    matching_urls = [loc.text for loc in locations if re.match(pattern, loc.text)]
    logger.info(matching_urls)


def parsing_csv():
    # Открываем CSV-файл с помощью pandas
    df = pd.read_csv(output_csv_file, nrows=10)

    # Просмотр первых 10 строк
    logger.info(df.head(10))


if __name__ == "__main__":
    # get_html()
    parsing()
    # get_json()
    # download_xml()
    # parsing_xml()
    # fetch_and_save()
    # parsing_csv()
