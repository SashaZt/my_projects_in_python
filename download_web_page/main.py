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
        "PHPSESSID": "c95e174e4800458653c20b9dc207596e",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        # 'cookie': 'PHPSESSID=c95e174e4800458653c20b9dc207596e',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://clarity-project.info/edr/37542726",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://clarity-project.info/edr/37542726/finances",
        cookies=cookies,
        headers=headers,
        proxies=proxies_dict,
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


def parsing():
    with open("proba.html", encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")

    # Список кодов
    codes = [
        "1012",
        "1195",
        "1495",
        "1595",
        "1621",
        "1695",
        "1900",
        "2350",
        "2000",
        "2280",
        "2285",
        "2505",
        "2510",
    ]

    # Список для хранения всех единиц данных
    all_results = []

    # Получаем заголовок страницы
    page_title = soup.select_one(
        "body > div.entity-page-wrap > div.entity-content-wrap > div.entity-header.px-10 > div:nth-child(3) > a"
    ).text.replace("#", "")

    # Ищем количество работников
    number_of_employees = None
    employee_label = soup.find("td", string="Кількість працівників")
    if employee_label:
        number_of_employees = employee_label.find_next_sibling("td").string.strip()

    # Ищем КАТОТТГ
    katottg = None
    katottg_label = soup.find("td", string="КАТОТТГ")
    if katottg_label:
        katottg = katottg_label.find_next_sibling("td").string.strip()

    # Словарь для текущей единицы данных
    results = {
        "page_title": page_title,
        "number_of_employees": number_of_employees,
        "katottg": katottg,
    }
    nobr_start = soup.select_one(
        "body > div.entity-page-wrap > div.entity-content-wrap > div.entity-content > table:nth-child(6) > thead > tr > th:nth-child(3) > span"
    ).text.strip()
    nobr_end = soup.select_one(
        "body > div.entity-page-wrap > div.entity-content-wrap > div.entity-content > table:nth-child(6) > thead > tr > th:nth-child(4) > span"
    ).text.strip()
    # Проходим по каждой строке таблицы
    for row in soup.select("tbody tr"):
        # Извлекаем код строки (находится во втором столбце)
        code_cell = row.select_one("td:nth-child(2)")

        if code_cell and code_cell.text.strip() in codes:
            code = code_cell.text.strip()

            # Извлекаем значения для начала и конца года
            beginning_of_year = row.select_one("td:nth-child(3)").text.strip()
            end_of_year = row.select_one("td:nth-child(4)").text.strip()

            # Сохраняем значения в словарь
            results[f"beginning_of_the_year_{code}"] = beginning_of_year
            results[f"end_of_the_year_{code}"] = end_of_year

    # Добавляем словарь в список all_results
    all_results.append(results)

    # Выводим список словарей
    print(nobr_start, nobr_end)

    # Пример записи в Excel через pandas
    df = pd.DataFrame(all_results)
    df.to_excel("financial_data.xlsx", index=False, engine="openpyxl")
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
    # parsing()
    # get_json()
    # download_xml()
    # parsing_xml()
    # fetch_and_save()
    parsing_csv()
