import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
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


def save_urls_product(output_csv_file, all_product_links):
    url_data = pd.DataFrame(all_product_links, columns=["url"])
    url_data.to_csv(output_csv_file, index=False)


# # Сбор информации о товарах
# product_details = []


# def collect_details():
#     with ThreadPoolExecutor(max_workers=20) as executor:
#         results = executor.map(fetch_product_details, all_product_links)
#         for detail in results:
#             if detail:
#                 product_details.append(detail)


if __name__ == "__main__":
    start_time = time.time()
    logger.info("Сбор ссылок на товары...")
    all_product_links = collect_links()
    logger.info(f"Найдено {len(all_product_links)} товаров.")
    save_urls_product(output_csv_file, all_product_links)

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
