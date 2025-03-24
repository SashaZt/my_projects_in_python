import json
import re
import sys
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger
from main_html import main_scraper

current_directory = Path.cwd()
data_directory = current_directory / "data"
html_directory = current_directory / "html"
log_directory = current_directory / "log"
img_directory = current_directory / "img"

img_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

html_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"
output_json_file = data_directory / "output.json"
BASE_URL = "https://altstar.ua/"

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


def get_html():
    cookies = {
        "PHPSESSID": "4u34v9cjpr22r449jev8j5ho40",
        "language": "uk-ua",
        "currency": "UAH",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        # 'cookie': 'PHPSESSID=4u34v9cjpr22r449jev8j5ho40; PHPSESSID=4u34v9cjpr22r449jev8j5ho40; PHPSESSID=4u34v9cjpr22r449jev8j5ho40; language=uk-ua; currency=UAH',
    }

    response = requests.get(
        "https://altstar.ua/1986se3754/bosch",
        cookies=cookies,
        headers=headers,
        timeout=30,
    )
    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open(output_html_file, "w", encoding="utf-8") as file:
            file.write(response.text)
        logger.info(f"Successfully saved {output_html_file}")
    else:
        logger.error(f"Failed to get HTML. Status code: {response.status_code}")


# def scrap_html():
#     # Пройтись по каждому HTML файлу в папке
#     # Initialize dictionaries for each section
#     left_column_data = {}
#     middle_column_data = {}
#     right_column_data = {}
#     for html_file in html_directory.glob("*.html"):
#         with html_file.open(encoding="utf-8") as file:
#             content = file.read()

#         # Create BeautifulSoup object
#         soup = BeautifulSoup(content, "lxml")

#         # Find the main product-info div
#         product_info = soup.find("div", class_="product-info")

#         if not product_info:
#             return {"error": "Product info div not found"}

#         # =============================================
#         # Extract from first column (left)
#         # =============================================
#         left_column = product_info.find("div", class_="col-sm-3 col-xs-12")

#         if left_column:
#             # Extract product name from ribbon
#             ribbon_name = left_column.find("h2", class_="ribbon_name single_product")
#             if ribbon_name:
#                 # Получаем текст и удаляем крайние пробельные символы
#                 product_name = ribbon_name.text.strip()

#                 # Заменяем неразрывный пробел на подчеркивание
#                 product_name = product_name.replace("\xa0", "_").replace(" ", "_")

#                 # Альтернативный вариант, заменяющий все пробельные символы
#                 # product_name = ''.join(c if not c.isspace() else '_' for c in product_name)

#                 left_column_data["product_name"] = product_name

#             # Extract price
#             price_elem = left_column.find("span", id="price-old")
#             if price_elem:
#                 left_column_data["price"] = price_elem.text.strip()

#             # Extract all image links using a set to avoid duplicates
#             image_links = set()

#             # Main product image
#             main_image = left_column.find("a", class_="MagicZoom")
#             if main_image and "href" in main_image.attrs:
#                 image_links.add(main_image["href"])

#             # Thumbnail images in MagicScroll
#             magic_scroll = left_column.find("div", class_="MagicScroll")
#             if magic_scroll:
#                 thumbnails = magic_scroll.find_all("a")
#                 for thumb in thumbnails:
#                     if "href" in thumb.attrs:
#                         image_links.add(f'{BASE_URL}{thumb["href"]}')

#             # Other thumbnail images
#             other_thumbs = left_column.find_all("a", class_="mz-thumb")
#             for thumb in other_thumbs:
#                 if "href" in thumb.attrs:
#                     image_links.add('{BASE_URL}{thumb["href"]}')

#             left_column_data["image_links"] = list(image_links)

#         # =============================================
#         # Extract from middle column
#         # =============================================
#         middle_column = product_info.find("div", class_="col-sm-4 col-xs-12")

#         if middle_column:
#             # Extract brand
#             # Извлечение бренда
#             # Ищем span, который СОДЕРЖИТ текст "Бренд", а не полностью соответствует ему
#             brand_span = middle_column.find(
#                 "span", string=lambda text: text and "Бренд:" in text if text else False
#             )

#             if brand_span:
#                 # Находим ссылку <a> внутри span
#                 brand_link = brand_span.find("a")
#                 if brand_link:
#                     brand = brand_link.find("b")
#                     if brand:
#                         middle_column_data["brand"] = brand.text.strip()
#                         logger.info(f"Extracted brand from link: {brand.text.strip()}")
#                 else:
#                     # Если нет ссылки, ищем просто тег <b>
#                     brand = brand_span.find("b")
#                     if brand:
#                         middle_column_data["brand"] = brand.text.strip()
#                         logger.info(f"Extracted brand from span: {brand.text.strip()}")
#             else:
#                 # Запасной вариант: ищем любой span с содержимым про бренд
#                 for span in middle_column.find_all("span"):
#                     if span.text and "Бренд:" in span.text:
#                         # Находим тег <b> в любом месте внутри этого span
#                         brand = span.find("b")
#                         if brand:
#                             middle_column_data["brand"] = brand.text.strip()
#                             break

#             name_product = middle_column.find("span", class_="product_cat_name prodttl")
#             if name_product:
#                 middle_column_data["name_product"] = name_product.text.strip()
#             # Extract characteristics
#             chars_div = middle_column.find("div", class_="attrs table")
#             if chars_div:
#                 characteristics = {}
#                 char_rows = chars_div.find_all("div", class_="detail-chars")

#                 for row in char_rows:
#                     title_div = row.find("div", class_="detail-chars-title")
#                     field_div = row.find("div", class_="detail-chars-field")

#                     if title_div and field_div:
#                         title = title_div.find("span", class_="detail-chars-title-name")
#                         if title:
#                             char_name = title.text.strip()
#                             char_value = field_div.text.strip()
#                             characteristics[char_name] = char_value

#                 middle_column_data["characteristics"] = characteristics

#             # Extract "Застосовується в агрегатах" data
#             aggregates_div = middle_column.find("div", class_="product-applicability")
#             if aggregates_div:
#                 aggregates_parts = []

#                 for div in aggregates_div.find_all("div", recursive=False):
#                     brand_elem = div.find("span", class_="s-s")
#                     if brand_elem and brand_elem.find("b"):
#                         brand_name = brand_elem.find("b").text.strip().rstrip(":")

#                         # Get all links (part numbers) for this brand
#                         links = div.find("div", class_="more").find_all("a")
#                         part_numbers = [link.text.strip() for link in links]

#                         # Format as requested: Brand:part1!part2!part3
#                         if part_numbers:
#                             aggregates_parts.append(
#                                 f"{brand_name}:{'!'.join(part_numbers)}"
#                             )

#                 # Join all brands with /
#                 middle_column_data["Застосовується в агрегатах"] = "/".join(
#                     aggregates_parts
#                 )

#         # =============================================
#         # Extract from right column
#         # =============================================
#         right_column = product_info.find("div", class_="col-sm-5 col-xs-12")

#         if right_column:
#             # Extract "Номери аналогів"
#             analogs_div = right_column.find("div", class_="analogs")
#             if analogs_div:
#                 analogs_parts = []

#                 # Find all brand sections
#                 for div in analogs_div.find_all("div", recursive=False):
#                     if div.find("span") and div.find("span").find("b"):
#                         brand_name = div.find("span").find("b").text.strip().rstrip(":")

#                         # Extract part numbers from links
#                         part_numbers = []
#                         for a_tag in div.find_all("a"):
#                             part_numbers.append(a_tag.text.strip())

#                         # Format as requested: Brand:part1!part2!part3
#                         if part_numbers:
#                             analogs_parts.append(
#                                 f"{brand_name}:{'!'.join(part_numbers)}"
#                             )

#                 # Join all brands with /
#                 right_column_data["Номери аналогів"] = "/".join(analogs_parts)

#             # Extract "Застосування по автомобілю"
#             applications_div = right_column.find("div", class_="by_car")
#             if applications_div:
#                 applications_span = applications_div.find("span")
#                 if applications_span:
#                     applications_text = applications_span.text.strip()

#                     # Process the applications text to merge by manufacturer
#                     lines = [
#                         line.strip()
#                         for line in applications_text.split("\n")
#                         if line.strip()
#                     ]

#                     # Process the applications text to merge by manufacturer
#                     # Get raw text from the span
#                     raw_text = applications_span.get_text()

#                     # Process the raw text to identify manufacturer patterns
#                     import re

#                     # Split the raw text into lines for processing
#                     lines = [
#                         line.strip() for line in raw_text.split("\n") if line.strip()
#                     ]

#                     # Dictionary to store manufacturer -> models mapping
#                     manufacturer_models = {}

#                     # Process each line
#                     for line in lines:
#                         # Identify manufacturer - first all uppercase word in the line
#                         match = re.match(r"^([A-Z]+)\s", line)
#                         if match:
#                             manufacturer = match.group(1)
#                             model_info = line[len(manufacturer) :].strip()

#                             if manufacturer not in manufacturer_models:
#                                 manufacturer_models[manufacturer] = []

#                             manufacturer_models[manufacturer].append(model_info)

#                     # Format as requested
#                     applications = []
#                     for manufacturer, models in manufacturer_models.items():
#                         models_text = "!".join(models)
#                         applications.append(f"{manufacturer} {models_text}")

#                     right_column_data["Застосування по автомобілю"] = applications


#         # Combine all data
#         result = {
#             "left_column": left_column_data,
#             "middle_column": middle_column_data,
#             "right_column": right_column_data,
#         }
#     with open(output_json_file, "w", encoding="utf-8") as f:
#         json.dump(result, f, ensure_ascii=False, indent=4)
#     return result
# Если нужно сохранить в список словарей или файл, вот пример:
def scrap_html():
    # Список для хранения данных всех товаров
    all_products = []

    # Счетчик обработанных файлов для логирования
    processed_files = 0
    total_files = 0

    # Подсчитаем общее количество HTML файлов во всех папках
    for html_path in html_directory.glob("**/*.html"):
        total_files += 1

    logger.info(f"Найдено всего HTML файлов: {total_files}")

    # Обходим все папки внутри html_directory и ищем HTML файлы
    for html_path in html_directory.glob("**/*.html"):
        try:
            logger.info(
                f"Обработка файла ({processed_files + 1}/{total_files}): {html_path}"
            )

            with html_path.open(encoding="utf-8") as file:
                content = file.read()

            # Initialize dictionaries for each section
            left_column_data = {}
            middle_column_data = {}
            right_column_data = {}

            # Create BeautifulSoup object
            soup = BeautifulSoup(content, "lxml")

            # Find the main product-info div
            product_info = soup.find("div", class_="product-info")

            if not product_info:
                logger.warning(
                    f"Не найден div с классом product-info в файле {html_path}"
                )
                processed_files += 1
                continue

            # =============================================
            # Extract from first column (left)
            # =============================================
            left_column = product_info.find("div", class_="col-sm-3 col-xs-12")

            if left_column:
                # Extract product name from ribbon
                ribbon_name = left_column.find(
                    "h2", class_="ribbon_name single_product"
                )
                if ribbon_name:
                    # Получаем текст и удаляем крайние пробельные символы
                    product_name = ribbon_name.text.strip()

                    # Заменяем неразрывный пробел на подчеркивание
                    product_name = product_name.replace("\xa0", "_").replace(" ", "_")

                    left_column_data["product_name"] = product_name

                # Extract price
                price_elem = left_column.find("span", id="price-old")
                if price_elem:
                    left_column_data["price"] = price_elem.text.strip()

                # Extract all image links using a set to avoid duplicates
                image_links = set()

                # Main product image
                main_image = left_column.find("a", class_="MagicZoom")
                if main_image and "href" in main_image.attrs:
                    image_links.add(main_image["href"])

                # Thumbnail images in MagicScroll
                magic_scroll = left_column.find("div", class_="MagicScroll")
                if magic_scroll:
                    thumbnails = magic_scroll.find_all("a")
                    for thumb in thumbnails:
                        if "href" in thumb.attrs:
                            image_links.add(f'{BASE_URL}{thumb["href"]}')

                # Other thumbnail images
                other_thumbs = left_column.find_all("a", class_="mz-thumb")
                for thumb in other_thumbs:
                    if "href" in thumb.attrs:
                        image_links.add(f'{BASE_URL}{thumb["href"]}')

                left_column_data["image_links"] = list(image_links)

            # =============================================
            # Extract from middle column
            # =============================================
            middle_column = product_info.find("div", class_="col-sm-4 col-xs-12")

            if middle_column:
                # Extract brand
                brand_span = middle_column.find(
                    "span",
                    string=lambda text: text and "Бренд:" in text if text else False,
                )

                if brand_span:
                    # Находим ссылку <a> внутри span
                    brand_link = brand_span.find("a")
                    if brand_link:
                        brand = brand_link.find("b")
                        if brand:
                            middle_column_data["brand"] = brand.text.strip()
                    else:
                        # Если нет ссылки, ищем просто тег <b>
                        brand = brand_span.find("b")
                        if brand:
                            middle_column_data["brand"] = brand.text.strip()
                else:
                    # Запасной вариант: ищем любой span с содержимым про бренд
                    for span in middle_column.find_all("span"):
                        if span.text and "Бренд:" in span.text:
                            # Находим тег <b> в любом месте внутри этого span
                            brand = span.find("b")
                            if brand:
                                middle_column_data["brand"] = brand.text.strip()
                                break

                name_product = middle_column.find(
                    "span", class_="product_cat_name prodttl"
                )
                if name_product:
                    middle_column_data["name_product"] = name_product.text.strip()

                # Extract characteristics
                chars_div = middle_column.find("div", class_="attrs table")
                if chars_div:
                    characteristics = {}
                    char_rows = chars_div.find_all("div", class_="detail-chars")

                    for row in char_rows:
                        title_div = row.find("div", class_="detail-chars-title")
                        field_div = row.find("div", class_="detail-chars-field")

                        if title_div and field_div:
                            title = title_div.find(
                                "span", class_="detail-chars-title-name"
                            )
                            if title:
                                char_name = title.text.strip()
                                char_value = field_div.text.strip()
                                characteristics[char_name] = char_value

                    middle_column_data["characteristics"] = characteristics

                # Extract "Застосовується в агрегатах" data
                aggregates_div = middle_column.find(
                    "div", class_="product-applicability"
                )
                if aggregates_div:
                    aggregates_parts = []

                    for div in aggregates_div.find_all("div", recursive=False):
                        brand_elem = div.find("span", class_="s-s")
                        if brand_elem and brand_elem.find("b"):
                            brand_name = brand_elem.find("b").text.strip().rstrip(":")

                            # Get all links (part numbers) for this brand
                            links = div.find("div", class_="more").find_all("a")
                            part_numbers = [link.text.strip() for link in links]

                            # Format as requested: Brand:part1!part2!part3
                            if part_numbers:
                                aggregates_parts.append(
                                    f"{brand_name}:{'!'.join(part_numbers)}"
                                )

                    # Join all brands with /
                    middle_column_data["aggregates"] = "/".join(aggregates_parts)

            # =============================================
            # Extract from right column
            # =============================================
            right_column = product_info.find("div", class_="col-sm-5 col-xs-12")

            if right_column:
                # Extract "Номери аналогів"
                analogs_div = right_column.find("div", class_="analogs")
                if analogs_div:
                    analogs_parts = []

                    # Find all brand sections
                    for div in analogs_div.find_all("div", recursive=False):
                        if div.find("span") and div.find("span").find("b"):
                            brand_name = (
                                div.find("span").find("b").text.strip().rstrip(":")
                            )

                            # Extract part numbers from links
                            part_numbers = []
                            for a_tag in div.find_all("a"):
                                part_numbers.append(a_tag.text.strip())

                            # Format as requested: Brand:part1!part2!part3
                            if part_numbers:
                                analogs_parts.append(
                                    f"{brand_name}:{'!'.join(part_numbers)}"
                                )

                    # Join all brands with /
                    right_column_data["analogs"] = "/".join(analogs_parts)

                # Extract "Застосування по автомобілю"
                applications_div = right_column.find("div", class_="by_car")
                if applications_div:
                    applications_span = applications_div.find("span")
                    if applications_span:
                        # Get raw text from the span
                        raw_text = applications_span.get_text()

                        # Split the raw text into lines for processing
                        lines = [
                            line.strip()
                            for line in raw_text.split("\n")
                            if line.strip()
                        ]

                        # Dictionary to store manufacturer -> models mapping
                        manufacturer_models = {}

                        # Process each line
                        for line in lines:
                            # Identify manufacturer - first all uppercase word in the line
                            match = re.match(r"^([A-Z]+)\s", line)
                            if match:
                                manufacturer = match.group(1)
                                model_info = line[len(manufacturer) :].strip()

                                if manufacturer not in manufacturer_models:
                                    manufacturer_models[manufacturer] = []

                                manufacturer_models[manufacturer].append(model_info)

                        # Format as requested
                        applications = []
                        for manufacturer, models in manufacturer_models.items():
                            models_text = "!".join(models)
                            applications.append(f"{manufacturer} {models_text}")

                        right_column_data["applications"] = applications

            # Combine all data
            product_data = {
                "left_column": left_column_data,
                "middle_column": middle_column_data,
                "right_column": right_column_data,
            }

            # Добавляем данные о товаре в общий список
            all_products.append(product_data)
            processed_files += 1

            # Периодически сохраняем данные, чтобы не потерять результаты при сбое
            if processed_files % 100 == 0:
                temp_output = output_json_file.with_name(
                    f"temp_output_{processed_files}.json"
                )
                with open(temp_output, "w", encoding="utf-8") as f:
                    json.dump(all_products, f, ensure_ascii=False, indent=4)
                logger.info(f"Сохранен промежуточный результат: {temp_output}")

        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_path}: {str(e)}")
            processed_files += 1
            continue

    # Сохраняем полный результат
    with open(output_json_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)

    logger.info(f"Всего обработано файлов: {processed_files}/{total_files}")
    logger.info(f"Данные сохранены в файл: {output_json_file}")

    return all_products


def sanitize_filename(filename: str) -> str:
    """Заменяет запрещённые символы в имени файла на подчёркивание."""
    # Список запрещённых символов в Windows
    forbidden_chars = r'\/:*?"<>|'
    # Создаём регулярное выражение для замены любого из этих символов
    # Заменяем каждый запрещённый символ на '_'
    sanitized = re.sub(f"[{re.escape(forbidden_chars)}]", "_", filename)
    return sanitized


def get_img(img_url, product_name):
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        # 'cookie': 'PHPSESSID=4u34v9cjpr22r449jev8j5ho40; PHPSESSID=4u34v9cjpr22r449jev8j5ho40; language=uk-ua; currency=UAH',
    }
    """
    Скачивает изображения по списку URL и возвращает список имен файлов.
    Пропускает скачивание, если файл уже существует.
    """
    all_data = []

    for i, url in enumerate(img_url):
        product_result = sanitize_filename(product_name)
        output_img_file = img_directory / f"{product_result}_{i}.jpg"
        name_img = f"{product_result}_{i}.jpg"

        # Проверяем, существует ли файл
        if output_img_file.exists():
            logger.info(f"Файл уже существует, пропускаю скачивание: {output_img_file}")
            all_data.append(name_img)
            continue  # Пропускаем запрос и переходим к следующему URL

        # Если файл не существует, скачиваем его
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                with open(output_img_file, "wb") as file:
                    file.write(response.content)
                logger.info(f"Сохранил: {output_img_file}")
                all_data.append(name_img)
            else:
                logger.error(
                    f"Failed to get image {i}. Status code: {response.status_code}"
                )
        except Exception as e:
            logger.error(f"Ошибка при скачивании изображения {i}: {str(e)}")

    return all_data


# def convert_json_to_csv():
#     """
#     Convert JSON product data to CSV format

#     Args:
#         json_file_path (str): Path to the JSON file
#         csv_file_path (str): Path to save the CSV file
#     """
#     # Load JSON data
#     with open(output_json_file, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     # Extract data from each section
#     left_column = data.get("left_column", {})
#     middle_column = data.get("middle_column", {})
#     right_column = data.get("right_column", {})

#     # Create a dictionary for the CSV row
#     row_data = {}

#     # Add product name and price
#     product_name = left_column.get("product_name", "")
#     row_data["Артикул"] = product_name
#     img_url = left_column.get("image_links", "")
#     img_list = get_img(img_url, product_name)
#     # For analogs, join all entries
#     row_data["Номера аналогів"] = right_column.get("Номери аналогів", "")

#     # Add aggregates, analogs, and applications
#     row_data["Застосованість"] = middle_column.get("Застосовується в агрегатах", "")

#     # For applications, join all entries with a separator
#     applications = right_column.get("Застосування по автомобілю", [])
#     if applications:
#         row_data["Застосованість авто"] = "||".join(applications)
#     else:
#         row_data["Застосованість авто"] = ""
#     name_product = middle_column.get("name_product", "")
#     row_data["Назва товару"] = name_product
#     brand = middle_column.get("brand", None)
#     row_data["Виробник"] = brand
#     row_data["Ціна"] = left_column.get("price", "")
#     row_data["Фото"] = ",".join(img_list)
#     row_data["Кількість"] = "100"

#     # Add all characteristics as separate columns
#     characteristics = middle_column.get("characteristics", {})
#     for key, value in characteristics.items():
#         # Clean column name for CSV
#         clean_key = key.replace(",", "").strip()
#         row_data[clean_key] = value

#     # Create DataFrame with a single row
#     df = pd.DataFrame([row_data])
#     output_csv_file = data_directory / "output.csv"
#     # Save to CSV
#     df.to_csv(output_csv_file, index=False, encoding="windows-1251", sep=";")

#     logger.info(f"CSV file created: {output_csv_file}")


def convert_json_to_csv():
    """
    Convert JSON product data (array of dictionaries) to CSV format and split into multiple files if exceeds 4000 rows

    Args:
        json_file_path (str): Path to the JSON file
        csv_file_path (str): Path to save the CSV file
    """
    # Load JSON data
    with open(output_json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # List to store all rows
    rows = []

    # Iterate over each item in the JSON array
    for item in data:
        # Extract data from each section of the current item
        left_column = item.get("left_column", {})
        middle_column = item.get("middle_column", {})
        right_column = item.get("right_column", {})

        # Create a dictionary for the CSV row
        row_data = {}

        # Add product name and price
        product_name = left_column.get("product_name", "")
        row_data["Артикул"] = product_name
        img_url = left_column.get("image_links", "")
        img_list = get_img(img_url, product_name)
        # For analogs, join all entries
        row_data["Номера аналогів"] = right_column.get("Номери аналогів", "")

        # Add aggregates, analogs, and applications
        row_data["Застосованість"] = middle_column.get("Застосовується в агрегатах", "")

        # For applications, join all entries with a separator
        applications = right_column.get("Застосування по автомобілю", [])
        if applications:
            row_data["Застосованість авто"] = "||".join(applications)
        else:
            row_data["Застосованість авто"] = ""
        name_product = middle_column.get("name_product", "")
        row_data["Назва товару"] = name_product
        brand = middle_column.get("brand", None)
        row_data["Виробник"] = brand
        row_data["Ціна"] = left_column.get("price", "")
        row_data["Фото"] = ",".join(img_list)
        row_data["Кількість"] = "100"

        # Add all characteristics as separate columns
        characteristics = middle_column.get("characteristics", {})
        for key, value in characteristics.items():
            # Clean column name for CSV
            clean_key = key.replace(",", "").strip()
            row_data[clean_key] = value

        # Append the row to the list
        rows.append(row_data)

    # Create DataFrame from all rows
    df = pd.DataFrame(rows)

    # Define base output path
    base_output_path = data_directory / "output"

    # Check if DataFrame exceeds 4000 rows
    rows_per_file = 4000
    if len(df) > rows_per_file:
        # Split DataFrame into chunks
        total_files = (len(df) + rows_per_file - 1) // rows_per_file
        for i in range(total_files):
            start_idx = i * rows_per_file
            end_idx = min((i + 1) * rows_per_file, len(df))
            df_chunk = df.iloc[start_idx:end_idx]
            output_csv_file = base_output_path.with_name(f"output_part_{i+1}.csv")
            df_chunk.to_csv(
                output_csv_file, index=False, encoding="windows-1251", sep=";"
            )
            logger.info(f"CSV file created: {output_csv_file}")
    else:
        # Single file if less than 4000 rows
        output_csv_file = base_output_path.with_suffix(".csv")
        df.to_csv(output_csv_file, index=False, encoding="windows-1251", sep=";")
        logger.info(f"CSV file created: {output_csv_file}")


if __name__ == "__main__":
    main_scraper()
    scrap_html()
    convert_json_to_csv()
