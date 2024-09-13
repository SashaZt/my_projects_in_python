from pathlib import Path
import requests
import gzip
import shutil
import csv
import random
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from configuration.logger_setup import logger
import threading
from bs4 import BeautifulSoup
import re

# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
data_directory = current_directory / "data"
gz_directory = current_directory / "gz"
xml_directory = current_directory / "xml"
html_directory = current_directory / "html"

data_directory.mkdir(parents=True, exist_ok=True)
gz_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)

xml_sitemap = data_directory / "sitemap_index.xml"
csv_url_site_maps = data_directory / "url_site_maps.csv"
csv_url_products = data_directory / "url_products.csv"
csv_file_successful = data_directory / "urls_successful.csv"

cookies = {
    "cf_clearance": "MbPIoPbSAHefbElXIQNSCNTLGuSxV0EHab4cVKRebSk-1726118903-1.2.1.1-J2LyAl13laqyZ3SF9CMqFJ9emjfge6dg_N2QwNl.0sX3R20dX2EmWuw0C198N.ccfTRZCXugoQ5r_Xsn1CAwIc7uNhqu2hkWDz1zGntJ1e3qcq_X3vhC1Nsz612lkinDR20kSiEu0F5N67oqcUapP572nvgzdi2DC26.UmMajqKUp23QvtDG0VmklFDUfy.HxtlAo3YSHu3w_MCZiyb.WatXXtDcx7c0GYOcZ1I9D2kJKkTX7Dsi7pv_QH1Rk2lKOeqnfsdwJjINGsjWqTIkj2jnhA3Zsyi743jZJbMzGAk16jeEXd_ECABBgVER_XYtaQDt13tMOiKwFQG7s1TnlZoHGdOj6aoE3TckYeDsb4nGZClA6IdyMMcv4xfXCqxuHPKqqD6qQiGF6GKrkvndcXebGs6a3Ugmid4GfhIT1rYIfT7vEvP6DDAvC1rNvdbK",
    "form_key": "7MtDJOzkzcuHmy6c",
    "mage-cache-storage": "{}",
    "mage-cache-storage-section-invalidation": "{}",
    "mage-cache-sessid": "true",
    "recently_viewed_product": "{}",
    "recently_viewed_product_previous": "{}",
    "recently_compared_product": "{}",
    "recently_compared_product_previous": "{}",
    "product_data_storage": "{}",
    "mage-messages": "",
    "__zlcmid": "1Nin0vbbCzKn1Ud",
}


headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies




def download_file(url, output_path):
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    response = requests.get(
        url,
        cookies=cookies,
        headers=headers,
        proxies=proxies_dict,
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
        for row in data:
            writer.writerow([row])


# 3. Скачивание всех .xml.gz файлов в многопоточном режиме
def download_gz_files(links, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    def download_link(link):
        file_name = output_dir / Path(urlparse(link).path).name
        download_file(link, file_name)

    with ThreadPoolExecutor(max_workers=10) as executor:
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


# 5. Парсинг распакованных XML файлов и запись URL в CSV
def parse_product_urls(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    product_urls = [loc.text for loc in root.findall("ns:url/ns:loc", namespace)]
    return product_urls


def process_xml_files(input_dir, output_csv):
    input_dir = Path(input_dir)
    product_urls = []

    for xml_file in input_dir.glob("*.xml"):
        product_urls.extend(parse_product_urls(xml_file))

    write_csv(output_csv, product_urls)


# Чтение успешных URL из CSV-файла
def get_successful_urls(csv_file_successful):
    """Читает успешные URL из CSV-файла и возвращает их в виде множества."""
    if not Path(csv_file_successful).exists():
        return set()  # Если файл не существует, возвращаем пустое множество

    with open(csv_file_successful, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        successful_urls = {row[0] for row in reader if row}  # Собираем URL в множество
    return successful_urls


# Функция для записи в CSV
def write_to_csv(url, csv_file_successful):
    with open(csv_file_successful, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([url])  # Записываем URL в CSV файл


# Функция для загрузки HTML с использованием прокси и записи успешных URL
def download_file_html(
    url, output_path, successful_urls, sync_counter, sync_frequency=10
):
    fetch_lock = threading.Lock()  # Локальная блокировка для многопоточности

    # Проверяем, был ли URL уже успешно обработан
    if url in successful_urls:
        logger.info(f"| Объявление уже было обработано, пропускаем: {url} |")
        return

    try:
        # Выполняем запрос к URL
        response = requests.get(
            url,
            cookies=cookies,  # Замените на актуальные cookies, если нужно
            headers=headers,  # Замените на актуальные headers, если нужно
            timeout=10,  # Устанавливаем таймаут на запрос
        )

        if response.status_code == 200:
            response.raise_for_status()  # Проверка на ошибки запроса

            # Сохраняем HTML контент в файл
            output_path.write_text(response.text, encoding="utf-8")
            logger.info(f"Downloaded: {url}")

            # Обновляем успешные URL
            with fetch_lock:
                successful_urls.add(url)
                sync_counter[0] += 1  # Увеличиваем счетчик синхронизации

                # Периодическая запись успешных URL
                if sync_counter[0] >= sync_frequency:
                    sync_successful_urls(successful_urls, csv_file_successful)
                    sync_counter[0] = 0  # Сбрасываем счетчик после синхронизации

        else:
            logger.error(f"Unexpected status code {response.status_code} for {url}")
            return  # Прекращаем выполнение функции, если статус не 200

    except requests.RequestException as e:
        logger.error(f"Failed to download {url}  {e}")


def sync_successful_urls(successful_urls, csv_file_successful):
    """Записывает все URL из множества successful_urls в CSV файл."""
    with open(csv_file_successful, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for url in successful_urls:
            writer.writerow([url])
    logger.info("Синхронизация успешных URL завершена.")


# Чтение URL из CSV файла
def load_urls_from_csv(csv_file):
    urls = []
    with open(csv_file, "r", encoding="utf-8") as file:
        for line in file:
            urls.append(line.strip())
    logger.info("Все ссылки загруженны")
    return urls


# Многопоточная загрузка страниц
def download_html_files(urls, output_dir, num_threads=15, sync_frequency=2):
    successful_urls = get_successful_urls(csv_file_successful)  # Читаем успешные URL
    sync_counter = [
        0
    ]  # Счетчик для синхронизации, используем список для изменения по ссылке

    def download_task(url):
        file_name = url.split("/")[-1]  # Получаем имя файла из URL
        if not file_name.endswith(".html"):
            file_name += ".html"  # Добавляем расширение, если его нет
        file_path = output_dir / file_name  # Генерация полного пути для сохранения
        download_file_html(
            url, file_path, successful_urls, sync_counter, sync_frequency
        )

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(download_task, urls)

    # Финальная синхронизация после завершения всех потоков
    sync_successful_urls(successful_urls, csv_file_successful)


# Функция для парсинга одного HTML файла
def parse_html_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    (
        page_title,
        price_wrapper,
        sku,
        brand,
        part,
        upc,
        url,
        min_order_qty,
        stock,
        date_1,
        date_2,
    ) = (
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )

    # 1. Извлечение заголовка (page_title) и MPN
    h1_tag = soup.select_one('h1.page-title[data-ui-id="page-title-wrapper"]')
    if h1_tag:
        full_title = h1_tag.text.strip()
        if "MPN:" in full_title:
            page_title = full_title.split("MPN:")[0].strip()
        else:
            page_title = full_title

    # 2. Извлечение цены (price_wrapper)
    price_tag = soup.select_one('span[data-price-type="finalPrice"] .price')
    if price_tag:
        price_wrapper = price_tag.text.strip()

    # 3. Извлечение SKU
    sku_tag = soup.select_one("div.product.attribute.sku .value")
    if sku_tag:
        sku = sku_tag.text.strip()

    # 4. Извлечение информации о продукте: brand, part, upc
    product_info_div = soup.select_one("div#product_info")
    if product_info_div:
        product_info_text = product_info_div.get_text(separator=" ").strip()
        if "Brand:" in product_info_text:
            brand = product_info_text.split("Brand:")[1].split("Part #:")[0].strip()
        if "Part #:" in product_info_text:
            part = product_info_text.split("Part #:")[1].split("UPC:")[0].strip()
        if "UPC:" in product_info_text:
            upc = product_info_text.split("UPC:")[1].strip()

    # 5. Извлечение URL (канонической ссылки)
    canonical_tag = soup.select_one('link[rel="canonical"]')
    if canonical_tag:
        url = canonical_tag.get("href")

    # 6. Извлечение минимального количества заказа (for Minimum Order Qty of 10)
    min_order_tag = soup.find_all("span")
    for tag in min_order_tag:
        if tag.text and "for Minimum Order Qty of" in tag.text:
            min_order_text = tag.text.strip()
            # Извлекаем число после "for Minimum Order Qty of"
            min_order_qty = min_order_text.split("for Minimum Order Qty of")[-1].strip()
            break  # Прерываем цикл, когда найдено минимальное количество заказа

    # 7. Извлечение наличия товара и дат
    pricing_info_div = soup.select_one("div#pricing_info")
    if pricing_info_div:
        pricing_text = pricing_info_div.get_text(separator=" ").strip()

        # Поиск наличия товара (In Stock)
        stock_match = re.search(r"In Stock \((\d+)\)", pricing_text)
        if stock_match:
            stock = f"In Stock ({stock_match.group(1)})"
        elif "In Stock" in pricing_text:
            stock = "In Stock"

        # Поиск даты доставки
        date_match_single = re.search(
            r"Expected to ship by (\w+ \d{1,2}, \d{4})", pricing_text
        )
        date_match_range = re.search(
            r"Expected to ship between (\w+ \d{1,2}, \d{4}) and (\w+ \d{1,2}, \d{4})",
            pricing_text,
        )

        if date_match_single:
            # Преобразуем дату в формат MM/DD/YYYY
            date_1 = re.sub(
                r"(\w+) (\d{1,2}), (\d{4})", r"\1/\2/\3", date_match_single.group(1)
            )
        elif date_match_range:
            # Преобразуем обе даты в формат MM/DD/YYYY
            date_1 = re.sub(
                r"(\w+) (\d{1,2}), (\d{4})", r"\1/\2/\3", date_match_range.group(1)
            )
            date_2 = re.sub(
                r"(\w+) (\d{1,2}), (\d{4})", r"\1/\2/\3", date_match_range.group(2)
            )

    # Логирование данных для проверки
    logger.info(f"Stock: {stock}")
    logger.info(f"Date 1: {date_1}")
    logger.info(f"Date 2: {date_2}")

    return {
        "url": url,
        "page_title": page_title,
        "price_wrapper": price_wrapper,
        "sku": sku,
        "brand": brand,
        "part": part,
        "upc": upc,
        "min_order_qty": min_order_qty,
        "stock": stock,
        "date_1": date_1,
        "date_2": date_2,
    }


# # Функция для парсинга всех файлов в директории
# def parse_html_directory(directory):
#     parsed_data = []
#     html_files = Path(directory).glob("*.html")

#     for html_file in html_files:
#         data = parse_html_file(html_file)
#         parsed_data.append(data)
#         # logger.info(f"Parsed {html_file}: {data}")

#     return parsed_data


# Функция для парсинга до 100 файлов в директории
def parse_html_directory(directory, max_files=1000):
    parsed_data = []
    html_files = Path(directory).glob("*.html")

    # Счётчик для ограничения количества файлов
    file_count = 0

    for html_file in html_files:
        if file_count >= max_files:
            break  # Останавливаем, когда достигнем 100 файлов

        data = parse_html_file(html_file)
        parsed_data.append(data)
        file_count += 1
        # logger.info(f"Parsed {html_file}: {data}")

    return parsed_data


def write_to_csv_data(data, csv_file):
    # Определяем заголовки (ключи из словарей)
    fieldnames = [
        "url",
        "page_title",
        "price_wrapper",
        "sku",
        "brand",
        "part",
        "upc",
        "min_order_qty",
    ]

    # Открываем файл для записи с разделителем ";"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")

        # Записываем заголовок
        writer.writeheader()

        # Записываем каждую строку данных
        for row in data:
            writer.writerow(row)

    print(f"Data written to {csv_file}")


# Основная функция, объединяющая все шаги
def main():
    # Шаг 1: Скачать основной файл sitemap-index.xml
    download_file(SITEMAP_INDEX_URL, xml_sitemap)

    # Шаг 2: Парсинг и запись ссылок в CSV
    sitemap_links = parse_sitemap_index(xml_sitemap)
    write_csv(csv_url_site_maps, sitemap_links)

    # Шаг 3: Скачивание .xml.gz файлов
    download_gz_files(sitemap_links, gz_directory)

    # Шаг 4: Распаковка .gz файлов
    extract_gz_files(gz_directory, xml_directory)

    # Шаг 5: Парсинг URL продуктов из XML файлов
    process_xml_files(xml_directory, csv_url_products)

    urls = load_urls_from_csv(csv_url_products)  # Загружаем URL из CSV
    
    download_html_files(
        urls, html_directory, num_threads=15
    )  # Скачиваем с использованием 10 потоков

    parsed_results = parse_html_directory(html_directory)
    # Запись в CSV файл
    # csv_file = "parsed_results.csv"
    # write_to_csv_data(parsed_results, csv_file)


if __name__ == "__main__":
    main()
