import asyncio
import csv
import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import openpyxl
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from PIL import Image

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
page_path = os.path.join(temp_path, "page")
html_path = os.path.join(temp_path, "html")
json_path = os.path.join(temp_path, "json")
img_path = os.path.join(temp_path, "img")


# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(page_path, exist_ok=True)
os.makedirs(html_path, exist_ok=True)
os.makedirs(json_path, exist_ok=True)
os.makedirs(img_path, exist_ok=True)

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}


def sanitize_json(json_string):
    # Заменяем контрольные символы, но сохраняем пробелы
    sanitized = re.sub(r"[^\x20-\x7E\n\t]", "", json_string)
    # Убираем лишние пробелы и переносы строк только внутри значений
    sanitized = re.sub(r"\s+", " ", sanitized)
    sanitized = re.sub(r'"\s+', '"', sanitized)
    sanitized = re.sub(r'\s+"', '"', sanitized)
    return sanitized


def extract_breadcrumb_list(soup):
    breadcrumb_script = soup.find(
        "script",
        attrs={"type": "application/ld+json"},
        string=lambda string: "BreadcrumbList" in string,
    )

    if breadcrumb_script:
        try:
            # print(breadcrumb_script)
            # sanitized_json = sanitize_json(breadcrumb_script.string)
            json_data = json.loads(breadcrumb_script.string)
            return json_data
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга BreadcrumbList: {e}")
            return None
    else:
        return None


def extract_data_breadcrumb(json_data):
    brand_product = ""
    category_product = ""
    breadcrumb = ""

    for item in json_data["itemListElement"]:
        if item["position"] == 1:
            brand_product = item["item"]["name"]
        elif item["position"] == 2:
            category_product = item["item"]["name"]
        elif item["position"] == 3:
            breadcrumb = item["item"]["name"]

    return brand_product, category_product, breadcrumb


def extract_product(soup):
    product_script = soup.find(
        "script",
        attrs={"type": "application/ld+json"},
        string=lambda string: "Product" in string,
    )

    if product_script:
        try:
            # sanitized_json = sanitize_json(product_script.string)
            json_data = json.loads(product_script.string)
            return json_data
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга Product: {e}")
            return None
    else:
        return None


def fetch(url, headers):
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def parsing(soup):
    product_json = extract_product(soup)
    if product_json is None:
        return None
    breadcrumb_json = extract_breadcrumb_list(soup)
    brand_product, category_product, breadcrumb = extract_data_breadcrumb(
        breadcrumb_json
    )

    name_product = product_json.get("name")
    image_product = product_json.get("image")
    url_product = product_json.get("url")
    sku_product = product_json.get("sku")
    price_product = product_json.get("offers", {}).get("price")

    data = {
        "breadcrumb": breadcrumb,
        "brand_product": brand_product,
        "category_product": category_product,
        "image_product": image_product,
        "sku_product": sku_product,
        "price_product": price_product,
        "name_product": name_product,
        "url_product": url_product,
    }
    return data


def parse_url(url, headers, filename_json):
    src = fetch(url, headers)
    soup = BeautifulSoup(src, "lxml")
    json_data = parsing(soup)
    if json_data and not os.path.exists(filename_json):
        with open(filename_json, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)
    return json_data


def main():
    urls = []
    with open("urls.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            urls.append(row["url"])

    # Замените на свой User-Agent
    headers = {"User-Agent": "Your User Agent String"}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for url in urls:
            filename_json = os.path.join(
                json_path, f"data_{hashlib.md5(url.encode()).hexdigest()}.json"
            )
            if not os.path.exists(filename_json):
                futures.append(executor.submit(parse_url, url, headers, filename_json))
            else:
                print(f"Файл для {url} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            # Здесь вы можете обрабатывать результаты по мере их завершения
            results.append(future.result())


def read_json_files():
    all_data = []
    for filename in os.listdir(json_path):
        if filename.endswith(".json"):
            file_path = os.path.join(json_path, filename)
            with open(file_path, "r", encoding="utf-8") as json_file:
                try:
                    data = json.load(json_file)
                    all_data.append(data)
                except json.JSONDecodeError as e:
                    print(f"Ошибка при чтении файла {filename}: {e}")
    return all_data


async def parsing_page():
    all_datas = read_json_files()
    # Преобразуем словарь обратно в список
    # unique_all_datas = list(all_datas.values())

    # Преобразование списка словарей в DataFrame
    df = pd.DataFrame(all_datas)

    # Сортировка по указанным колонкам
    df = df.sort_values(by=["breadcrumb", "brand_product", "category_product"])

    # Создаем новый Workbook
    wb = Workbook()
    ws = wb.active

    # Записываем заголовки
    for col_num, column_title in enumerate(df.columns, 1):
        ws.cell(row=1, column=col_num, value=column_title)

    # Записываем данные и вставляем изображения
    for row_num, row_data in enumerate(df.itertuples(index=False), 2):
        for col_num, cell_value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=cell_value)

            # Если это колонка с изображениями, вставляем изображение
            if col_num == df.columns.get_loc("image_product") + 1:
                image_url = cell_value
                try:
                    image_filename = os.path.join(
                        img_path, f"{row_num}.jpg"
                    )  # Изменим на .jpg
                    webp_filename = os.path.join(
                        img_path, f"{row_num}.webp"
                    )  # Временный файл для WebP

                    if not os.path.exists(image_filename):
                        print(
                            f"Загрузка изображения: {image_url}"
                        )  # Отладочное сообщение
                        image_data = requests.get(
                            image_url, headers=headers, timeout=30
                        ).content

                        # Сохраняем как WebP, даже если оно такое
                        with open(webp_filename, "wb") as img_file:
                            img_file.write(image_data)

                        # Конвертируем WebP в JPEG
                        with Image.open(webp_filename) as img:
                            img.convert("RGB").save(image_filename, "JPEG")

                        os.remove(webp_filename)  # Удаляем временный WebP файл

                    image = openpyxl.drawing.image.Image(image_filename)
                    image.width = 250  # Ширина изображения
                    image.height = 250  # Высота изображения
                    ws.add_image(image, cell.coordinate)
                    ws.row_dimensions[row_num].height = (
                        image.height
                    )  # Установка высоты строки
                except Exception as e:
                    print(f"Ошибка при загрузке изображения {image_url}: {e}")

    # Сохраняем файл
    output_file = "output.xlsx"
    wb.save(output_file)

    print(f"Файл сохранен как {output_file}")


if __name__ == "__main__":
    main()
    asyncio.run(parsing_page())
