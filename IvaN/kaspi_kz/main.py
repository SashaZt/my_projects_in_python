import json
import sys
from pathlib import Path
import pandas as pd
import requests
from loguru import logger
import csv
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
import pandas as pd
import requests
from loguru import logger

current_directory = Path.cwd()
json_category_directory = current_directory / "json_category"
log_directory = current_directory / "log"
data_directory = current_directory / "data"
html_directory = current_directory / "html"
html_id_directory = current_directory / "html_id"

html_id_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
json_category_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
output_csv_file = data_directory / "output.csv"
output_id_csv_file = data_directory / "output_id.csv"

BASE_URL = "https://kaspi.kz"
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # 'Cookie': 'layout=d; dt-i=env=production|ssrVersion=v1.18.39|pageMode=catalog; ks.tg=47; k_stat=a6864b24-87cc-4ce5-94ea-db68e661c075; current-action-name=Index; kaspi.storefront.cookie.city=750000000',
    "DNT": "1",
    "Pragma": "no-cache",
    "Referer": "https://kaspi.kz/shop/c/categories/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

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


def get_json_category():

    cookies = {
        "ks.tg": "47",
        "k_stat": "a6864b24-87cc-4ce5-94ea-db68e661c075",
        "current-action-name": "Index",
        "kaspi.storefront.cookie.city": "750000000",
    }

    headers = {
        "Accept": "application/json, text/*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        # 'Cookie': 'ks.tg=47; k_stat=a6864b24-87cc-4ce5-94ea-db68e661c075; current-action-name=Index; kaspi.storefront.cookie.city=750000000',
        "DNT": "1",
        "Referer": "https://kaspi.kz/shop/c/categories/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "X-KS-City": "750000000",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    codes = [
        "Smartphones and gadgets",
        "Home equipment",
        "TV_Audio",
        "Computers",
        "Furniture",
        "Beauty care",
        "Child goods",
        "Pharmacy",
        "Construction and repair",
        "Sports and outdoors",
        "Leisure",
        "Car goods",
        "Jewelry and Bijouterie",
        "Fashion accessories",
        "Fashion",
        "Shoes",
        "Pet goods",
        "Home",
        "Gifts and party supplies",
        "Office and school supplies",
    ]
    for code in codes:
        logger.info(code)
        params = {
            "depth": "2",
            "city": "750000000",
            "code": code,
            "rootType": "desktop",
        }
        json_category_file = json_category_directory / f"{code}.json"
        if json_category_file.exists():
            continue
        response = requests.get(
            "https://kaspi.kz/yml/main-navigation/n/n/desktop-menu",
            params=params,
            cookies=cookies,
            headers=headers,
            timeout=30,
        )

        # Проверка успешности запроса
        if response.status_code == 200:
            json_data = response.json()
            with open(json_category_file, "w", encoding="utf-8") as f:
                json.dump(
                    json_data, f, ensure_ascii=False, indent=4
                )  # Записываем в файл
            logger.info(json_category_file)
        else:
            logger.error(response.status_code)


def scrap_json_category():
    all_data = []
    for json_file in json_category_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        subnodes_level_01 = data.get("subNodes", None)
        if subnodes_level_01:
            for level_02 in subnodes_level_01:
                subnodes_level_02 = level_02.get("subNodes", None)
                if subnodes_level_02:
                    for level_03 in subnodes_level_02:
                        subnodes_level_03 = level_03.get("link", None)
                        url = f"{BASE_URL}{subnodes_level_03}"
                        all_data.append(url)

    # Создать DataFrame из списка URL
    df = pd.DataFrame(all_data, columns=["url"])

    # Записать DataFrame в CSV файл
    df.to_csv(output_csv_file, index=False)


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


def fetch(url):
    cookies = {
        "layout": "d",
        "dt-i": "env=production|ssrVersion=v1.18.39|pageMode=catalog",
        "ks.tg": "47",
        "k_stat": "a6864b24-87cc-4ce5-94ea-db68e661c075",
        "current-action-name": "Index",
        "kaspi.storefront.cookie.city": "750000000",
    }

    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logger.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logger.error(f"An error occurred: {err}")
        return None
    return response.text


def get_html(url, html_file):
    src = fetch(url)
    if src:
        with open(html_file, "w", encoding="utf-8") as file:
            file.write(src)
        logger.info(f"HTML saved to {html_file}")


def main_th_id():
    ids = []
    with open(output_id_csv_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ids.append(row["url"])

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for id_site in ids:
            output_html_file = (
                html_id_directory
                / f"html_{hashlib.md5(id_site.encode()).hexdigest()}.html"
            )

            if not os.path.exists(output_html_file):
                futures.append(executor.submit(get_html_id, id_site, output_html_file))
            else:
                logger.warning(f"Файл для {id} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            # Здесь вы можете обрабатывать результаты по мере их завершения
            results.append(future.result())


def fetch_id(merchantId):
    cookies = {
        "layout": "d",
        "dt-i": "env=production|ssrVersion=v1.18.39|pageMode=merchant",
        "ks.tg": "47",
        "k_stat": "a6864b24-87cc-4ce5-94ea-db68e661c075",
        "current-action-name": "Index",
        "kaspi.storefront.cookie.city": "750000000",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 'Cookie': 'layout=d; dt-i=env=production|ssrVersion=v1.18.39|pageMode=merchant; ks.tg=47; k_stat=a6864b24-87cc-4ce5-94ea-db68e661c075; current-action-name=Index; kaspi.storefront.cookie.city=750000000',
        "DNT": "1",
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

    try:
        url = f"https://kaspi.kz/shop/info/merchant/{merchantId}/address-tab/"
        logger.info(url)
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(response.status_code)
    except requests.exceptions.HTTPError as err:
        logger.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logger.error(f"An error occurred: {err}")
        return None
    return response.text


def get_html_id(url, html_file):
    src = fetch_id(url)
    if src:
        with open(html_file, "w", encoding="utf-8") as file:
            file.write(src)
        logger.info(f"HTML saved to {html_file}")


def scrap_html():
    all_data = set()
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Используем регулярное выражение для поиска данных allMerchants
        pattern = re.compile(r'\{"id":"(:allMerchants:[^"]+)",.*?\}', re.DOTALL)
        matches = pattern.findall(content)

        # Создаем список словарей с найденными данными
        all_merchants = []
        for match in matches:
            merchant_pattern = re.compile(
                r'\{"id":"' + re.escape(match) + r'",.*?\}', re.DOTALL
            )
            merchant_data = merchant_pattern.search(content)
            if merchant_data:
                all_merchants.append(json.loads(merchant_data.group(0)))

        # Выводим результаты
        for merchant in all_merchants:
            id_site = merchant["id"].replace(":allMerchants:", "")
            all_data.add(id_site)
        # Создать DataFrame из списка URL
    df = pd.DataFrame(all_data, columns=["url"])

    # Записать DataFrame в CSV файл
    df.to_csv(output_id_csv_file, index=False)


if __name__ == "__main__":
    # Скачиваем все категории
    # get_json_category()
    # Получаем ссылки на все категории 3 уровня
    # scrap_json_category()
    # main_th()
    # scrap_html()
    main_th_id()
