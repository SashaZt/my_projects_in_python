from pathlib import Path
import pandas as pd
import requests
import gzip
import shutil
import csv
import random
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from configuration.logger_setup import logger
import threading
from bs4 import BeautifulSoup
import re
import base64
from io import BytesIO
import requests
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET

import threading
import datetime
import json

# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
data_directory = current_directory / "data"
gz_directory = current_directory / "gz"
xml_directory = current_directory / "xml"
# html_directory = current_directory / "html"

data_directory.mkdir(parents=True, exist_ok=True)
gz_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
# html_directory.mkdir(parents=True, exist_ok=True)

xml_sitemap = data_directory / "sitemap_index.xml"
csv_url_site_maps = data_directory / "url_site_maps.csv"
csv_url_products = data_directory / "url_products.csv"
csv_file_successful = data_directory / "urls_successful.csv"
csv_result = data_directory / "result.csv"
txt_cookies = current_directory / "cookies.txt"


headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}


# 1. Скачать основной файл sitemap-index.xml
SITEMAP_INDEX_URL = (
    "https://www.govets.com/sitemap-index.xml"  # замените ссылку на реальную
)


# def load_all_cookies_from_file() -> dict:
#     # Открываем файл и загружаем данные как JSON
#     with txt_cookies.open("r", encoding="utf-8") as f:
#         cookies_data = json.load(f)

#     # Создаем пустой словарь для всех cookies
#     cookies = {}


#     # Итерируем по списку cookies и сохраняем их в словарь
#     for cookie in cookies_data:
#         cookies[cookie["name"]] = cookie["value"]
#     return cookies
def load_all_cookies_from_file() -> dict:
    # Открываем файл и читаем содержимое построчно
    cookies = {}
    with txt_cookies.open("r", encoding="utf-8") as f:
        for line in f:
            # Игнорируем пустые строки и скобки
            line = line.strip()
            if not line or line in ["{", "}"]:
                continue

            # Убираем лишние запятые в конце строки
            if line.endswith(","):
                line = line[:-1]

            # Разделяем ключ и значение
            if ":" in line:
                name, value = line.split(":", 1)

                # Убираем пробелы и кавычки
                name = name.strip().strip("'").strip('"')
                value = value.strip().strip("'").strip('"')

                # Добавляем куку в словарь
                cookies[name] = value

    return cookies


def download_file(url, output_path, cookies):

    response = requests.get(
        url,
        cookies=cookies,
        headers=headers,
    )
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
    else:
        raise Exception(
            f"Failed to download {url}. Status code: {response.status_code}"
        )


# 2. Парсинг sitemap-index.xml и запись в CSV файл
def parse_sitemap_index(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_links = [loc.text for loc in root.findall("ns:sitemap/ns:loc", namespace)]
    return sitemap_links


def write_csv(file_path, data):
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Записываем заголовок
        writer.writerow(["url"])

        # Записываем данные
        for row in data:
            writer.writerow([row])


# 3. Скачивание всех .xml.gz файлов в многопоточном режиме
def download_gz_files(links, output_dir, cookies):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    def download_link(link):
        file_name = output_dir / Path(urlparse(link).path).name
        download_file(link, file_name, cookies)

    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(download_link, links)


# 4. Распаковка .xml.gz файлов
def extract_gz_files(input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for gz_file in input_dir.glob("*.gz"):
        output_file = output_dir / gz_file.stem  # Убираем ".gz"
        with gzip.open(gz_file, "rb") as f_in:
            with open(output_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)


def process_xml_files(input_dir, output_csv):
    input_dir = Path(input_dir)
    product_urls = []

    for xml_file in input_dir.glob("*.xml"):
        product_urls.extend(parse_product_urls(xml_file))

    write_csv(output_csv, product_urls)


# 5. Парсинг распакованных XML файлов и запись URL в CSV
def parse_product_urls(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    product_urls = [loc.text for loc in root.findall("ns:url/ns:loc", namespace)]
    return product_urls


# Чтение URL из CSV файла
def load_urls_from_csv(csv_file):
    urls = []
    with open(csv_file, "r", encoding="utf-8") as file:
        for line in file:
            urls.append(line.strip())
    logger.info("Все ссылки загруженны")
    return urls


# Основная функция, объединяющая все шаги
def main(cookies):
    # Шаг 1: Скачать основной файл sitemap-index.xml
    download_file(SITEMAP_INDEX_URL, xml_sitemap, cookies)
    logger.info("Скачали основной файл sitemap")

    # Шаг 2: Парсинг и запись ссылок в CSV
    sitemap_links = parse_sitemap_index(xml_sitemap)
    write_csv(csv_url_site_maps, sitemap_links)
    logger.info("Собрали ссылки для скачивания всех архивов gz")

    # Шаг 3: Скачивание .xml.gz файлов
    download_gz_files(sitemap_links, gz_directory, cookies)
    logger.info("Все архивы gz скачаны")

    # Шаг 4: Распаковка .gz файлов
    extract_gz_files(gz_directory, xml_directory)
    logger.info("Все архивы gz распакованы")  # Исправлено

    # Шаг 5: Парсинг URL продуктов из XML файлов
    process_xml_files(xml_directory, csv_url_products)
    logger.info("Получили все ссылки на товары")


def write_to_csv(data, filename):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{data}\n")


def get_successful_urls(csv_file_successful):
    """Читает успешные URL из CSV-файла и возвращает их в виде множества."""
    if not Path(csv_file_successful).exists():
        return set()

    with open(csv_file_successful, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        successful_urls = {row[0] for row in reader if row}
    return successful_urls


# 1. Извлечение заголовка (page_title) и MPN
def get_h1(soup):
    page_title = None
    h1_tag = soup.select_one('h1.page-title[data-ui-id="page-title-wrapper"]')
    if h1_tag:
        full_title = h1_tag.text.strip()
        if "MPN:" in full_title:
            page_title = full_title.split("MPN:")[0].strip()
        else:
            page_title = full_title
    return page_title


# 2. Извлечение цены (price_wrapper)
def get_price_wrapper(soup):
    price_wrapper = None
    price_tag = soup.select_one('span[data-price-type="finalPrice"] .price')
    if price_tag:
        price_wrapper = price_tag.text.strip()
    return price_wrapper


# 3. Извлечение SKU
def get_sku(soup):
    sku = None
    sku_tag = soup.select_one("div.product.attribute.sku .value")
    if sku_tag:
        sku = sku_tag.text.strip()
    return sku


# 4. Извлечение информации о продукте: brand, part, upc
def get_brand(soup):
    brand = None
    part = None
    upc = None
    product_info_div = soup.select_one("div#product_info")
    if product_info_div:
        product_info_text = product_info_div.get_text(separator=" ").strip()
        if "Brand:" in product_info_text:
            brand = product_info_text.split("Brand:")[1].split("Part #:")[0].strip()
        if "Part #:" in product_info_text:
            part = product_info_text.split("Part #:")[1].split("UPC:")[0].strip()
        if "UPC:" in product_info_text:
            upc = product_info_text.split("UPC:")[1].strip()
    return brand, part, upc


# 5. Извлечение URL (канонической ссылки)
def get_data_urk(soup):
    canonical_tag = soup.select_one('link[rel="canonical"]')
    if canonical_tag:
        url = canonical_tag.get("href")
    return url


# 6. Извлечение минимального количества заказа (for Minimum Order Qty of 10)
def get_min_order_qty(soup):
    min_order_qty = None
    min_order_tag = soup.find_all("span")
    for tag in min_order_tag:
        if tag.text and "for Minimum Order Qty of" in tag.text:
            min_order_text = tag.text.strip()
            # Извлекаем число после "for Minimum Order Qty of"
            min_order_qty = min_order_text.split("for Minimum Order Qty of")[-1].strip()
            break  # Прерываем цикл, когда найдено минимальное количество заказа
    return min_order_qty


# 7. Извлечение наличия товара и дат
def get_stock_data(sku):

    stock, date_1, date_2 = None, None, None  # Инициализируем переменные

    data = {
        "currentproduct": sku,
        "zipcode": "32937",
        "shipestimate": "1",
    }

    response = requests.post(
        "https://www.govets.com/Veratics_ShippingEstimate/index/view/",
        cookies=cookies,
        headers=headers,
        data=data,
    )
    if response.status_code == 200:
        # # Определяем тип ответа (HTML или JSON)
        # if "application/json" in response.headers.get("Content-Type", ""):
        #     # Ответ в формате JSON
        logger.info(response.text())
        json_data = response.json()

        # Теперь парсим HTML, который находится внутри ключа "output" в JSON
        if "output" in json_data:
            soup = BeautifulSoup(json_data["output"], "html.parser")
            # Используем soup для дальнейшего парсинга HTML
            # Например, вызываем нашу функцию для извлечения stock, date_1, date_2
            # 1. Извлечение информации о наличии товара (stock)
            stock_tag = soup.find("strong", text=re.compile(r"In Stock"))
            if stock_tag:
                stock_text = stock_tag.text.strip()
                # Если есть количество в скобках
                stock_match = re.search(r"In Stock \((\d+)\)", stock_text)
                if stock_match:
                    stock = f"In Stock ({stock_match.group(1)})"
                else:
                    stock = "In Stock"

            # 2. Извлечение даты (date_1, date_2)
            shipping_tag = soup.find(
                "strong", text=re.compile(r"Free Shipping\. Expected to ship")
            )
            if shipping_tag:
                shipping_text = shipping_tag.text.strip()
                # Поиск одной даты
                date_match_single = re.search(
                    r"Expected to ship by (\w+ \d{1,2}, \d{4})", shipping_text
                )
                # Поиск диапазона дат
                date_match_range = re.search(
                    r"Expected to ship between (\w+ \d{1,2}, \d{4}) and (\w+ \d{1,2}, \d{4})",
                    shipping_text,
                )

                if date_match_single:
                    # Преобразуем дату в формат MM/DD/YYYY
                    date_1 = re.sub(
                        r"(\w+) (\d{1,2}), (\d{4})",
                        r"\2/\1/\3",
                        date_match_single.group(1),
                    )
                elif date_match_range:
                    # Преобразуем обе даты в формат MM/DD/YYYY
                    date_1 = re.sub(
                        r"(\w+) (\d{1,2}), (\d{4})",
                        r"\2/\1/\3",
                        date_match_range.group(1),
                    )
                    date_2 = re.sub(
                        r"(\w+) (\d{1,2}), (\d{4})",
                        r"\2/\1/\3",
                        date_match_range.group(2),
                    )
        # Возвращаем результат
    return stock, date_1, date_2


def parsing(soup, url, csv_file_successful):
    parsing_lock = threading.Lock()  # Локальная блокировка

    try:
        page_title = None
        price_wrapper = None
        sku = None
        brand = None
        part = None
        upc = None
        min_order_qty = None
        stock = None
        date_1 = None
        date_2 = None

        page_title = get_h1(soup)
        price_wrapper = get_price_wrapper(soup)
        sku = get_sku(soup)
        brand, part, upc = get_brand(soup)
        min_order_qty = get_min_order_qty(soup)
        # stock, date_1, date_2 = get_stock_data(sku)

        data = data = (
            f"{url};{page_title};{price_wrapper};{sku};{brand};{part};{upc};{min_order_qty}"
        )
        logger.info(data)
        write_to_csv(data, csv_result)
        return True
    except Exception as ex:
        logger.error(ex)


def fetch_url(url, headers, cookies, csv_file_successful, successful_urls):
    fetch_lock = threading.Lock()  # Локальная

    if url in successful_urls:
        logger.info(f"| Объявление уже было обработано, пропускаем. |")
        return

    try:
        response = requests.get(
            url,
            headers=headers,
            cookies=cookies,
            timeout=60,  # Тайм-аут для предотвращения зависания
        )
        # response.raise_for_status()
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            success = parsing(soup, url, csv_file_successful)
            if success:
                with fetch_lock:
                    successful_urls.add(url)
                    write_to_csv(url, csv_file_successful)
            return

        elif response.status_code == 403:
            logger.error("Ошибка 403: доступ запрещен. Возвращаемся к выбору действий.")
            return 403  # Возвращаем специальный код ошибки 403
        else:
            logger.error(f"Ошибка {response.status_code}")

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")


def get_html(cookies, max_workers):
    # Получение списка уже успешных URL
    successful_urls = get_successful_urls(csv_file_successful)

    urls_df = pd.read_csv(csv_url_products)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                fetch_url,
                url,
                headers,
                cookies,
                csv_file_successful,
                successful_urls,
            )
            for count, url in enumerate(urls_df["url"], start=1)
        ]

        for future in as_completed(futures):
            try:
                result = future.result()  # Получаем результат выполнения задачи
                if result == 403:
                    return (
                        403  # Возвращаем ошибку 403 для обработки в основной программе
                    )
            except Exception as e:
                logger.error(f"Error occurred: {e}")


# if __name__ == "__main__":
#     main()
#     get_html(max_workers=15)
def remove_successful_urls():
    # Проверяем, если файл с успешными URL пустой
    if csv_file_successful.stat().st_size == 0:
        logger.info("Файл urls_successful.csv пуст, ничего не делаем.")
        return

    # Загружаем данные из обоих CSV файлов
    try:
        # Читаем csv_url_products с заголовком
        df_products = pd.read_csv(csv_url_products)

        # Читаем csv_file_successful без заголовка и присваиваем имя столбцу
        df_successful = pd.read_csv(csv_file_successful, header=None, names=["url"])
    except FileNotFoundError as e:
        logger.error(f"Ошибка: {e}")
        return

    # Проверка на наличие столбца 'url' в df_products
    if "url" not in df_products.columns:
        logger.info("Файл url_products.csv не содержит колонку 'url'.")
        return

    # Удаляем успешные URL из списка продуктов
    initial_count = len(df_products)
    df_products = df_products[~df_products["url"].isin(df_successful["url"])]
    final_count = len(df_products)

    # Если были удалены какие-то записи
    if initial_count != final_count:
        # Перезаписываем файл csv_url_products
        df_products.to_csv(csv_url_products, index=False)
        logger.info(
            f"Удалено {initial_count - final_count} записей из {csv_url_products.name}."
        )

        # Очищаем файл csv_file_successful
        open(csv_file_successful, "w").close()
        logger.info(f"Файл {csv_file_successful.name} очищен.")
    else:
        print("Не было найдено совпадающих URL для удаления.")


while True:
    cookies = load_all_cookies_from_file()
    remove_successful_urls()
    # Запрос ввода от пользователя
    print(
        "Введите 1 для получения всех ссылок"
        "\nВведите 2 для получения данных в csv"
        "\nВведите 0 для закрытия программы"
    )
    user_input = int(input("Выберите действие: "))

    if user_input == 1:
        main(cookies)
    elif user_input == 2:
        max_workers = int(input("Введите количество потоков: "))
        result = get_html(cookies, max_workers)
        if result == 403:
            logger.info("Ошибка 403, Обнови cookies")
            continue  # Возвращаемся к выбору действий
    elif user_input == 0:
        print("Программа завершена.")
        break  # Выход из цикла, завершение программы
    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
