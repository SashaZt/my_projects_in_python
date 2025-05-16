import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from config.logger import logger

# Настройка путей
current_directory = Path.cwd()
config_directory = current_directory / "config"
temp_directory = current_directory / "temp"
html_directory = temp_directory / "html"
log_directory = current_directory / "log"

# Создание директорий, если они не существуют
log_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
temp_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)


# Файлы

config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"
log_file_path = log_directory / "log_message.log"

base_url = "https://bachasport.pl/katalog-produktow/"

cookies = {
    "eb51ed644d1374a0fe35cca1b42ee871": "kgs3qh8jqukn5fs5dt2t3pimrh",
    "cpnb_cookiesSettings": "%7B%7D",
    "cookiesDirective": "1",
    "_gcl_au": "1.1.1243353817.1747390406",
    "_fbp": "fb.1.1747390405784.706253638406852744",
    "_gid": "GA1.2.185498008.1747390406",
    "_ga": "GA1.2.1289585510.1747390405",
    "_ga_R6NPSRGEJZ": "GS2.1.s1747392850$o2$g1$t1747393720$j60$l0$h0",
}
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "referer": "https://bachasport.pl/katalog-produktow/bez+kategorii/adidas-training-hardware?limit=72&start=72",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}


def crawl_bachasport():
    # Создаем сессию и настраиваем ее один раз
    session = requests.Session()
    session.headers.update(headers)
    session.cookies.update(cookies)

    # Получаем все ссылки на категории
    category_links = get_category_links(base_url, session)
    logger.info(f"Found {len(category_links)} categories")

    # Получаем все ссылки на товары из всех категорий
    all_product_links = []
    for category_link in category_links:
        product_links = get_product_links_from_category(category_link, session)
        all_product_links.extend(product_links)
        logger.info(f"Found {len(product_links)} products in category: {category_link}")
        # Делаем паузу, чтобы не перегружать сервер
        time.sleep(1)

    logger.info(f"Found a total of {len(all_product_links)} unique products")

    # Скачиваем HTML-файлы для всех товаров
    main_th(all_product_links, session)

    return all_product_links


def get_category_links(base_url, session):
    """Extract all category links from the main catalog page"""
    category_links = []

    try:
        response = session.get(base_url)
        response.raise_for_status()
        src = response.text
        # Save the HTML content
        with open("file_page_file.html", "w", encoding="utf-8") as file:
            file.write(src)
        soup = BeautifulSoup(src, "lxml")

        # Находим все li с классом cf_filters_list_li
        li_elements = soup.find_all(
            "li",
            attrs={
                "class": "cf_filters_list_li",
                "id": re.compile("^cf_option_li_virtuemart_manufacturer"),
            },
        )

        # Для каждого li находим все ссылки
        for li in li_elements:
            a_elements = li.find_all("a")
            for element in a_elements:
                href = element.get("href")
                if href:
                    full_url = (
                        urljoin(base_url, href) + "?limit=72"
                    )  # Add limit parameter
                    category_links.append(full_url)

    except Exception as e:
        logger.error(f"Error extracting category links: {e}")

    return category_links


def get_product_links_from_category(category_url, session):
    """Extract all product links from a category page including pagination"""
    product_links = set()  # Use a set to avoid duplicates
    current_url = category_url

    while True:
        try:
            logger.info(f"Processing page: {current_url}")
            response = session.get(current_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            product_list_div = soup.find("div", attrs={"id": "product_list"})
            if product_list_div:
                title_divs = product_list_div.find_all("div", attrs={"class": "Title"})
                for title_div in title_divs:
                    a_elements = title_div.find_all("a")
                    for element in a_elements:
                        href = element.get("href")
                        if href:
                            full_url = urljoin(category_url, href)
                            product_links.add(full_url)
            else:
                logger.warning(
                    f"Не найден div с id='product_list' на странице {current_url}"
                )

            # Check if there's a next page button that is active
            next_page_link = None
            inactive_next = None

            # Ищем все элементы li
            li_elements = soup.find_all("li")
            for li in li_elements:
                # Проверяем, является ли это li с неактивной кнопкой "next"
                if "next-more" in li.get("class", []):
                    span = li.find("span")
                    if span:
                        inactive_next = li

                # Проверяем, является ли это li с активной кнопкой "next"
                a = li.find("a", attrs={"class": "next-more"})
                if a:
                    next_page_link = a

            if inactive_next:
                # Next page button is inactive, stop pagination
                break

            if next_page_link:
                # Get the href of the next page
                next_href = next_page_link.get("href")
                if next_href:
                    current_url = urljoin(category_url, next_href)
                    # Be nice to the server
                    time.sleep(1)
                else:
                    break
            else:
                break

        except Exception as e:
            logger.error(f"Error extracting product links from {current_url}: {e}")
            break

    return list(product_links)


# def download_product_html_files(product_links, session, headers, cookies):
#     """Download HTML files for all product links"""
#     # Create a directory to save HTML files

#     for index, url in enumerate(product_links):
#         try:
#             # # Extract product ID or name from URL for filename
#             # product_id = url.split("/")[-1]
#             # # Clean up the product ID to use as filename
#             # product_id = re.sub(r"[^\w]", "_", product_id)

#             output_html_file = (
#                 html_directory / f"html_{hashlib.md5(url.encode()).hexdigest()}.html"
#             )

#             logger.info(f"Downloading {url} to {output_html_file}")
#             response = session.get(url, headers=headers, cookies=cookies)
#             response.raise_for_status()
#             src = response.text
#             # Save the HTML content
#             with open(output_html_file, "w", encoding="utf-8") as file:
#                 file.write(src)
#             # Be nice to the server
#             time.sleep(1)

#         except Exception as e:
#             logger.error(f"Error downloading {url}: {e}")

#     logger.info(f"Downloaded HTML files for {len(product_links)} products")


def main_th(urls, session):
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for url in urls:
            output_html_file = (
                html_directory / f"html_{hashlib.md5(url.encode()).hexdigest()}.html"
            )
            if not output_html_file.exists():
                futures.append(
                    executor.submit(get_html, url, output_html_file, session)
                )
            else:
                logger.info(f"Файл для {url} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            results.append(future.result())


def get_html(url, html_file, session):
    src = fetch(url, session)

    if src is None:
        return url, html_file, False

    with open(html_file, "w", encoding="utf-8") as file:
        file.write(src)

    logger.info(f"Успешно загружен и сохранен: {html_file}")
    return url, html_file, True


def fetch(url, session):
    try:
        response = session.get(url, timeout=30, stream=True)

        # Проверка статуса ответа
        if response.status_code != 200:
            logger.warning(
                f"Статус не 200 для {url}. Получен статус: {response.status_code}. Пропускаем."
            )
            return None
        # Принудительно устанавливаем кодировку UTF-8
        response.encoding = "utf-8"
        return response.text

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при загрузке {url}: {str(e)}")
        return None


def parse_html_files_to_json():
    """
    Обрабатывает все HTML-файлы в директории html_directory,
    извлекает информацию о товарах и сохраняет в JSON-файл.
    """
    results = []
    html_files = list(html_directory.glob("*.html"))
    total_files = len(html_files)

    logger.info(f"Найдено {total_files} HTML-файлов для обработки")

    # Используем многопоточность для ускорения обработки
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Создаем список задач
        futures = [
            executor.submit(process_html_file, html_file) for html_file in html_files
        ]

        # Обрабатываем результаты по мере их завершения
        for i, future in enumerate(as_completed(futures)):
            try:
                product_info = future.result()
                if product_info:
                    results.append(product_info)

                # Логируем прогресс каждые 100 файлов
                if (i + 1) % 100 == 0 or (i + 1) == total_files:
                    logger.info(f"Обработано {i + 1}/{total_files} файлов")

            except Exception as e:
                logger.error(f"Ошибка при обработке файла: {e}")

    # Сохраняем результаты в JSON-файл
    output_json_file = temp_directory / "products_info.json"
    try:
        with open(output_json_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

        logger.info(
            f"Результаты сохранены в {output_json_file}. Всего обработано {len(results)} товаров"
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении JSON-файла: {e}")

    return results


def process_html_file(html_file):
    """
    Обрабатывает один HTML-файл и возвращает информацию о товаре.

    Args:
        html_file: путь к HTML-файлу

    Returns:
        dict: словарь с информацией о товаре и путь к исходному файлу
    """
    try:
        # Извлекаем имя файла без расширения
        file_hash = html_file.stem.replace("html_", "")

        # Читаем HTML-файл
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Парсим HTML
        soup = BeautifulSoup(html_content, "lxml")

        # Получаем основную информацию о товаре
        product_details = parse_product_details_minimal(soup)

        return product_details

    except Exception as e:
        logger.error(f"Ошибка при обработке файла {html_file}: {e}")
        return None


def parse_product_details_minimal(soup):
    """
    Парсит только доступность и символ товара из страницы.

    Args:
        soup: объект BeautifulSoup с HTML-страницей товара

    Returns:
        dict: словарь с доступностью и символом товара
    """
    product_details = {}

    try:
        # Находим основной блок с информацией о товаре
        content_div = soup.find("div", attrs={"id": "t3-content"})
        if content_div:
            fright_div = content_div.find("div", attrs={"class": "fright"})
            if fright_div:

                # Извлекаем доступность товара
                stock_div = fright_div.find("div", attrs={"class": "stock"})
                if stock_div:
                    # Удаляем жирный текст "Dostępność:" из блока
                    stock_text = stock_div.text.replace("Dostępność:", "").strip()
                    product_details["Dostępność Bacha.PL"] = stock_text

                # Извлекаем символ товара
                code_div = fright_div.find("div", attrs={"class": "code"})
                if code_div:
                    # Удаляем жирный текст "Symbol:" из блока
                    code_text = code_div.text.replace("Symbol:", "").strip()
                    product_details["Symbol"] = code_text

    except Exception as e:
        logger.error(f"Ошибка при парсинге деталей товара: {e}")

    return product_details


def merge_product_data_files():
    """
    Объединяет данные из двух JSON-файлов на основе поля "Symbol".
    За основу берется complete_products_data.json, а из products_info.json
    добавляется информация о наличии из поля "Dostępność Bacha.PL".

    Returns:
        list: список объединенных записей
    """
    # Пути к файлам
    complete_data_file = temp_directory / "complete_products_data.json"
    products_info_file = temp_directory / "products_info.json"
    result_file = temp_directory / "result.json"

    # Проверяем существование файлов
    if not complete_data_file.exists():
        logger.error(f"Файл {complete_data_file} не найден")
        return []

    if not products_info_file.exists():
        logger.error(f"Файл {products_info_file} не найден")
        return []

    try:
        # Читаем данные из основного файла
        with open(complete_data_file, "r", encoding="utf-8") as f:
            complete_data = json.load(f)
        logger.info(f"Загружено {len(complete_data)} записей из {complete_data_file}")

        # Читаем данные из файла с информацией о наличии
        with open(products_info_file, "r", encoding="utf-8") as f:
            products_info = json.load(f)
        logger.info(f"Загружено {len(products_info)} записей из {products_info_file}")

        # Создаем словарь для быстрого поиска по Symbol из products_info
        products_info_dict = {}
        for item in products_info:
            symbol = item.get("Symbol")
            if symbol:
                products_info_dict[symbol] = item.get(
                    "Dostępność Bacha.PL", "Информация о наличии отсутствует"
                )

        logger.info(
            f"Создан индекс по символам, найдено {len(products_info_dict)} уникальных символов"
        )

        # Объединяем данные
        merged_data = []
        matched_count = 0

        for item in complete_data:
            symbol = item.get("Symbol")
            if not symbol:
                logger.warning(f"Запись без символа в основном файле: {item}")
                continue

            merged_item = item.copy()  # Копируем исходные данные

            # Если символ найден во втором файле, добавляем данные о наличии
            if symbol in products_info_dict:
                merged_item["Dostępność Bacha.PL"] = products_info_dict[symbol]
                matched_count += 1
            else:
                # Символ не найден во втором файле
                merged_item["Dostępność Bacha.PL"] = "Не найдено на Bacha.PL"

            merged_data.append(merged_item)

        # Логируем статистику объединения
        logger.info(f"Всего обработано {len(merged_data)} записей из основного файла")
        logger.info(f"Найдено соответствий по символу: {matched_count}")
        logger.info(f"Не найдено соответствий: {len(merged_data) - matched_count}")

        # Сохраняем результат в новый файл
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Результат сохранен в {result_file}")

        return merged_data

    except Exception as e:
        logger.error(f"Ошибка при объединении файлов: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return []


if __name__ == "__main__":
    # Run the crawler
    # product_links = crawl_bachasport()
    # logger.info(f"Finished crawling with {len(product_links)} products")
    # Парсим все HTML-файлы и сохраняем результаты в JSON
    # parse_html_files_to_json()
    merge_product_data_files()
