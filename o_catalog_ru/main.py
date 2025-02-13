import asyncio
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
html_directory = current_directory / "html"
log_directory = current_directory / "log"
img_directory = current_directory / "img"
log_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
img_directory.mkdir(parents=True, exist_ok=True)

output_json_file = data_directory / "output.json"
output_xlsx_file = data_directory / "output.xlsx"
output_csv_file = data_directory / "output.csv"
output_csv_file_img = data_directory / "output_img.csv"
output_xml_file = data_directory / "output.xml"
log_file_path = log_directory / "log_message.log"

BASE_URL = "https://o-catalog.ru/product-category/scania/"
TOTAL_PAGES = 9722

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)

cookies = {
    "_ym_uid": "173935762064349998",
    "_ym_d": "1739357620",
    "_ym_isad": "2",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # 'Cookie': '_ym_uid=173935762064349998; _ym_d=1739357620; _ym_isad=2',
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def fetch_product_links(page_number):
    url = f"{BASE_URL}page/{page_number}/"
    attempts = 20
    for attempt in range(attempts):
        try:
            proxies = {
                "http": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
                "https": "http://scraperapi:6c54502fd688c7ce737f1c650444884a@proxy-server.scraperapi.com:8001",
            }
            response = requests.get(url, cookies=cookies, headers=headers, timeout=60)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "lxml")

                # Поиск ссылок на товары
                product_links = link_product(soup)
                logger.info(f"products on page {page_number}")
                return product_links
            else:
                logger.warning(
                    f"Non-200 status code {response.status_code} on attempt {attempt + 1} for page {page_number}. Retrying in 5 seconds..."
                )
                time.sleep(5)
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Request error fetching page {page_number} on attempt {attempt + 1}: {e}"
            )
            time.sleep(5)
        except Exception as e:
            logger.error(
                f"Unexpected error fetching page {page_number} on attempt {attempt + 1}: {e}"
            )
            time.sleep(5)
    return []


def link_product(soup):
    all_urls = set()
    for a in soup.select("div.thunk-product > a.woocommerce-LoopProduct-link"):
        url = a.get("href")
        all_urls.add(url)

    return all_urls


def fetch_product_details(product_url):
    try:
        response = requests.get(product_url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")

        # Пример извлечения данных (нужно настроить под реальную структуру страницы)
        title = (
            soup.select_one("h1.product_title").text.strip()
            if soup.select_one("h1.product_title")
            else "No Title"
        )
        price = (
            soup.select_one("p.price").text.strip()
            if soup.select_one("p.price")
            else "No Price"
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching product {product_url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching product {product_url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching product {product_url}: {e}")
        return None


def collect_links():
    # Сбор всех ссылок на товары
    all_product_links = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(fetch_product_links, range(1, TOTAL_PAGES + 1))
        for links in results:
            all_product_links.extend(links)
    return all_product_links


def save_urls_product(csv_file, all_product_links):
    url_data = pd.DataFrame(all_product_links, columns=["url"])
    url_data.to_csv(csv_file, index=False)


# # Сбор информации о товарах
# product_details = []


# def collect_details():
#     with ThreadPoolExecutor(max_workers=20) as executor:
#         results = executor.map(fetch_product_details, all_product_links)
#         for detail in results:
#             if detail:
#                 product_details.append(detail)
def main_th():
    urls = []
    with open(output_csv_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            urls.append(row["url"])

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for url in urls:
            output_html_file = (
                html_directory / f"html_{hashlib.md5(url.encode()).hexdigest()}.html"
            )

            if not os.path.exists(output_html_file):
                futures.append(executor.submit(get_html, url, output_html_file))
            else:
                print(f"Файл для {url} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            # Здесь вы можете обрабатывать результаты по мере их завершения
            results.append(future.result())


def main_th_img():
    urls = []
    with open(output_csv_file_img, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            urls.append(row["url"])

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for url in urls:
            image_filename = extract_image_filename(url)
            output_html_file = (
                html_directory / f"html_{hashlib.md5(url.encode()).hexdigest()}.html"
            )

            if not os.path.exists(output_html_file):
                futures.append(executor.submit(get_html, url, output_html_file))
            else:
                print(f"Файл для {url} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            # Здесь вы можете обрабатывать результаты по мере их завершения
            results.append(future.result())


def fetch(url):
    attempts = 10
    for attempt in range(attempts):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(
                    f"Non-200 status code {response.status_code} on attempt {attempt + 1} for URL {url}. Retrying in 5 seconds..."
                )
                time.sleep(5)
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Request error fetching URL {url} on attempt {attempt + 1}: {e}"
            )
            time.sleep(5)
    return None


def get_html(url, html_file):
    src = fetch(url)
    with open(html_file, "w", encoding="utf-8") as file:
        file.write(src)
    logger.info(html_file)


def extract_image_filename(image_url):
    match = re.search(r"/(\d{4})/(\d{2})/([^/]+)\.png$", image_url)
    if match:
        return f"{match.group(1)}_{match.group(2)}_{match.group(3)}"
    return "unknown_filename"


async def parsing_page():
    all_data = []
    all_img_urls = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(content, "lxml")
            name_tag = soup.find("h1", attrs={"class": "product_title entry-title"})
            name = name_tag.text.strip() if name_tag else None
            img_tag = soup.find("meta", attrs={"property": "og:image"})
            image_url = img_tag.get("content") if img_tag else None
            if not image_url:
                continue
            image_filename = extract_image_filename(image_url)
            description = None
            description_tag = soup.find("div", attrs={"id": "tab-description"})
            if description_tag:
                text_parts = description_tag.text.split("Данная деталь", 1)
                description = (
                    "Данная деталь" + text_parts[1].strip()
                    if len(text_parts) > 1
                    else None
                )
            else:
                description = None

            data_product = {
                "name": name,
                "description": description,
                "image_filename": image_filename,
            }
            all_data.append(data_product)
            all_img_urls.append(image_url)
    save_urls_product(output_csv_file_img, all_img_urls)
    df = pd.DataFrame(all_data)

    # Сохраняем в Excel
    df.to_excel(output_xlsx_file, index=False)


if __name__ == "__main__":
    start_time = time.time()
    logger.info("Сбор ссылок на товары...")
    # all_product_links = collect_links()
    # logger.info(f"Найдено {len(all_product_links)} товаров.")
    # save_urls_product(output_csv_file, all_product_links)
    # main_th()
    # asyncio.run(parsing_page())
    main_th_img()
# logger.info("Сбор информации о товарах...")
# collect_details()

# logger.info(f"Собрано данных о {len(product_details)} товарах.")
# logger.info(f"Время выполнения: {time.time() - start_time:.2f} секунд")

# # Пример вывода результата
# for product in product_details[:5]:
#     logger.info(product)

# with open("product_data.json", "w", encoding="utf-8") as f:
#     json.dump(product_details, f, ensure_ascii=False, indent=4)

# logger.info("Данные сохранены в product_data.json")
